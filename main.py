# import sys
# from extractor import PDFOutlineExtractor

# def main():
#     """
#     Main function to run the PDF outline extraction from the command line.
#     """
#     if len(sys.argv)!= 2:
#         print("Usage: python main.py <path_to_pdf_file>")
#         sys.exit(1)

#     pdf_path = sys.argv
    
#     try:
#         extractor = PDFOutlineExtractor(pdf_path)
#         json_output = extractor.extract_outline()
#         print(json_output)
#     except Exception as e:
#         # Create a JSON error message
#         error_output = json.dumps({
#             "title": f"Error processing {pdf_path}",
#             "outline":,
#             "error": str(e)
#         }, indent=4)
#         print(error_output)
#     finally:
#         if 'extractor' in locals() and extractor.doc:
#             extractor.close()

# if __name__ == "__main__":
#     main()


import sys
import json
from extractor import PDFOutlineExtractor

def main():
    """
    Main function to run the PDF outline extraction from the command line.
    """
    if len(sys.argv)!= 2:
        print("Usage: python main.py <path_to_pdf_file>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    extractor = None  # Initialize extractor to ensure it exists for the 'finally' block

    try:
        extractor = PDFOutlineExtractor(pdf_path)
        json_output = extractor.extract_outline()
        print(json_output)
    except Exception as e:
        # Create a JSON error message
        error_output = json.dumps({
            "title": f"Error processing {pdf_path}",
            "outline": [],  # This line has been corrected
            "error": str(e)
        }, indent=4)
        print(error_output)
    finally:
        # Safely close the document if it was opened
        if extractor and extractor.doc:
            extractor.close()

if __name__ == "__main__":
    main()