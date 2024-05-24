# AWS Textract Data Extraction Web Application

## Overview
This project involves creating a web application using Streamlit and AWS Textract to extract text, tables, key-value pairs, and dates from documents. The application supports both PDFs and image files (PNG, JPG, JPEG) and provides a user-friendly interface for uploading documents, processing them, and viewing the extracted information.

## Key Features
1. **Document Upload**: Users can upload PDF or image files through a file uploader widget.
2. **S3 Integration**: Uploaded files are temporarily stored in an S3 bucket for processing.
3. **AWS Textract Integration**: The application utilizes AWS Textract for:
   - **PDF Analysis**: Extracting tables and forms (key-value pairs) from PDFs.
   - **Image Text Detection**: Detecting and extracting text from image files.
4. **Data Extraction and Processing**:
   - **Lines of Text**: Extracted lines of text are displayed.
   - **Tables**: Extracted tables are formatted and displayed in a readable format.
   - **Key-Value Pairs**: Extracted key-value pairs are presented in a dictionary format.
   - **Date Extraction**: Dates found within the document are identified and displayed.
5. **Error Handling**: The application includes error handling for AWS and S3-related issues, ensuring users are informed of any problems.
6. **File Saving**: Users can save the extracted text, tables, key-value pairs, and dates to a text file for offline use.

## Technical Implementation
1. **Streamlit**: The application is built using Streamlit, a Python library for creating interactive web applications. Streamlit simplifies the process of creating a web interface for data-driven applications.
2. **AWS Textract**: The document analysis is performed using AWS Textract, which is called via the Boto3 library. Textract can extract structured data from documents, including text, tables, and key-value pairs.
3. **AWS S3**: Uploaded files are stored in an S3 bucket. This facilitates the use of Textract, which requires files to be in S3 for document analysis.
4. **Data Processing**:
   - **PDFs**: The application starts a Textract document analysis job and polls for the job status until completion. Once the analysis is complete, the response is processed to extract and organize the data.
   - **Images**: Textract's `detect_document_text` API is used for extracting text directly from image files.
5. **Data Display**:
   - **Lines**: All detected lines of text are displayed sequentially.
   - **Tables**: Extracted tables are processed into pandas DataFrames for easy manipulation and display.
   - **Key-Value Pairs**: Key-value pairs are extracted and displayed as a dictionary.
   - **Dates**: Dates found in the text lines are extracted and displayed.

## User Interaction
1. **File Upload**: Users can upload their documents via a simple file uploader.
2. **Processing Feedback**: The application provides feedback during processing, indicating whether the document is being analyzed or if an error has occurred.
3. **Results Display**: Once processing is complete, users can view the extracted text, tables, key-value pairs, and dates directly in the browser.
4. **Save Functionality**: Users can save the extracted data to a text file with a single click.

## Conclusion
This AWS Textract Data Extraction application showcases the integration of cloud services with a web interface to automate and simplify the extraction of structured data from documents. It demonstrates practical use of AWS Textract for document analysis, provides robust error handling, and ensures data is presented in a user-friendly manner. This project exemplifies the power of combining AWS services with Python-based web development for efficient and effective data processing solutions.
