import streamlit as st
import boto3
import pandas as pd
import time
import uuid
from io import BytesIO
from datetime import datetime
from botocore.exceptions import ClientError
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, BUCKET_NAME
from trp import Document

client = boto3.client('textract',
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name=AWS_REGION)

def upload_to_s3(file_bytes, original_filename):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
    bucket_name = BUCKET_NAME
    date_str = datetime.now().strftime("%Y-%m-%d")
    base_name, extension = original_filename.rsplit('.', 1)
    sanitized_base_name = base_name.replace(' ', '_')
    file_name = f'{sanitized_base_name}_{date_str}.{extension}'
    try:
        s3.upload_fileobj(BytesIO(file_bytes), bucket_name, file_name)
        return bucket_name, file_name
    except ClientError as e:
        st.error(f"Error uploading file to S3: {e}")
        return None, None

def extract_text_from_pdf(file_bytes, original_filename):
    bucket_name, file_name = upload_to_s3(file_bytes, original_filename)
    if not bucket_name or not file_name:
        return None
    
    try:
        response = client.start_document_analysis(
            DocumentLocation={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': file_name
                }
            },
            FeatureTypes=['TABLES', 'FORMS']
        )
        job_id = response['JobId']
        
        while True:
            response = client.get_document_analysis(JobId=job_id)
            status = response['JobStatus']
            if status in ['SUCCEEDED', 'FAILED']:
                break
            time.sleep(5)
        
        if status == 'FAILED':
            raise Exception("Document analysis failed")
        
        # Collect all pages of the response
        all_blocks = response['Blocks']
        next_token = response.get('NextToken', None)
        
        while next_token:
            response = client.get_document_analysis(JobId=job_id, NextToken=next_token)
            all_blocks.extend(response['Blocks'])
            next_token = response.get('NextToken', None)
        
        response['Blocks'] = all_blocks
        return response
    
    except ClientError as e:
        st.error(f"AWS Textract error: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

def extract_text_from_image(file_bytes):
    try:
        response = client.detect_document_text(Document={'Bytes': file_bytes})
        lines = [item['Text'] for item in response['Blocks'] if item['BlockType'] == 'LINE']
        return lines
    
    except ClientError as e:
        st.error(f"AWS Textract error: {e}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return []

def extract_text_from_image_table(file_bytes):
    try:
        response = client.detect_document_text(Document={'Bytes': file_bytes})
        blocks = response['Blocks']
        if not blocks:
            return []
        
        # Group blocks by their detected table IDs
        table_blocks = {}
        for block in blocks:
            if block['BlockType'] == 'TABLE':
                if 'Table' not in table_blocks:
                    table_blocks['Table'] = []
                table_blocks['Table'].append(block)
        
        if 'Table' not in table_blocks:
            return []
        
        # Process each detected table and extract text
        tables = []
        for table_block in table_blocks['Table']:
            rows = {}
            for relationship in table_block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        cell = blocks[child_id]
                        if cell['BlockType'] == 'CELL':
                            row_index = cell['RowIndex']
                            column_index = cell['ColumnIndex']
                            if row_index not in rows:
                                rows[row_index] = {}
                            rows[row_index][column_index] = cell['Text']
            
            # Convert rows into DataFrame for each table
            table_data = []
            for row_index in sorted(rows.keys()):
                row_data = [rows[row_index].get(column_index, '') for column_index in sorted(rows[row_index].keys())]
                table_data.append(row_data)
            
            df = pd.DataFrame(table_data)
            tables.append(df)
        
        return tables
    
    except ClientError as e:
        st.error(f"AWS Textract error: {e}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return []


def process_textract_response(response):
    try:
        # st.write("Textract Response:")
        # st.json(response)  # Log the full response for debugging

        if 'Blocks' not in response:
            raise ValueError("Response does not contain 'Blocks'")

        doc = Document(response)
        lines = [line.text for page in doc.pages for line in page.lines if line.text]
        tables = []
        key_values = {}

        for page in doc.pages:
            for table in page.tables:
                table_data = []
                for row in table.rows:
                    row_data = [cell.text if cell.text else "" for cell in row.cells]
                    table_data.append(row_data)
                df = pd.DataFrame(table_data)
                tables.append(df)

            for field in page.form.fields:
                key = field.key.text if field.key and field.key.text else ""
                value = field.value.text if field.value and field.value.text else ""
                key_values[key] = value

        date = next((line for line in lines if 'Date' in line), None)
        
        return lines, tables, key_values, date
    except Exception as e:
        st.error(f"Error processing Textract response: {e}")
        return [], [], {}, None

def main():
    st.title("AWS Textract Data Extraction")
    
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        original_filename = uploaded_file.name
        try:
            if uploaded_file.type == "application/pdf":
                st.write("Extracting text from PDF...")
                response = extract_text_from_pdf(file_bytes, original_filename)
                if response:
                    lines, tables, key_values, date = process_textract_response(response)
                else:
                    st.error("Error occurred during document analysis.")
            else:
                st.write("Extracting text from Image...")
                tables = extract_text_from_image_table(file_bytes)
                lines = extract_text_from_image(file_bytes)
                key_values, date = {}, None
            
                st.subheader("Extracted Text:")
                for line in lines:
                    st.write(line)

            if tables:
                st.subheader("Extracted Tables:")
                for i, table in enumerate(tables):
                    st.write(f"Table {i+1}:")
                    st.table(table)

            if key_values:
                st.subheader("Extracted Key-Value Pairs:")
                st.write(key_values)
    
            date_str = datetime.now().strftime("%Y-%m-%d")
            base_name, extension = original_filename.rsplit('.', 1)
            sanitized_base_name = base_name.replace(' ', '_')
            output_filename = f"{sanitized_base_name}_{date_str}.txt"

            if st.button("Save to File"):
                with open(output_filename, "w") as text_file:
                    text_file.write("Extracted Tables:\n")
                    for i, table in enumerate(tables):
                        text_file.write(f"Table {i+1}:\n")
                        text_file.write(table.to_string() + "\n\n")
                    text_file.write("Extracted Key-Value Pairs:\n")
                    for key, value in key_values.items():
                        text_file.write(f"{key}: {value}\n")
                    if date:
                        text_file.write(f"Date: {date}\n")
                st.success(f"Text saved to {output_filename}")
        
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
