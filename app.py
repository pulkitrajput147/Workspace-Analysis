import streamlit as st
import requests
import json
from PIL import Image
import io
import os
import base64
from io import BytesIO
import openai
from openai import OpenAI
import re
from dotenv import load_dotenv

# Method to analyze the image
def analyze_image(image):
    # Convert image to bytes
    def convert_base64(image):
        try:
            # If the image is already a PIL object, use BytesIO to get the bytes
            if isinstance(image, Image.Image):
                jpeg_buffer = BytesIO()
                image.convert("RGB").save(jpeg_buffer, format="JPEG")
                jpeg_bytes = jpeg_buffer.getvalue()
            else:
                # If the image is in raw bytes, use it directly
                jpeg_bytes = image

            # Convert the JPEG bytes to Base64
            canvas_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')
            return canvas_base64
        except Exception as e:
            print(f"Error in converting to base64: {e}")
            return None
    
    # Analyzing the image via gpt
    def gpt_analysis_agent(image):
        try:
            GPT_API_KEY = os.environ.get("LLM_API_KEY")
            client = OpenAI(api_key=GPT_API_KEY)
            response = client.chat.completions.create(
                    model='gpt-4o',
                    messages=[
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': f"""

                                        Analyze this workspace image in detail. Provide the following information:

                                        1. Object Identification:
                                        - Count and list the number of screens (monitors, laptops, etc.)
                                        - Count and identify the presence of laptops
                                        - Confirm the presence of a keyboard and mouse

                                        2. Back Support Analysis:
                                        - Examine the person's sitting position
                                        - Determine which parts of the back (upper, mid, lower) are in contact with the chair's back support
                                        - For each section (upper, mid, lower), specify whether it is "Supported" or "Not Supported"

                                        3. Distance from Screen Analysis:
                                        - Estimate the distance between the person and the nearest screen
                                        - Categorize this distance as either:
                                            "Less than one arm's length"
                                            "One arm's length"
                                            "More than one arm's length"

                                        4. Additional Observations:
                                        - Note any ergonomic issues or potential improvements in the setup
                                        - Comment on the overall workspace organization

                                        Please provide your analysis in a structured format that can be easily parsed. Use clear headings and bullet points for each section.( There should be no output before Object Identification)

                                        """,
                            },
                            {
                                'type': 'image_url',
                                'image_url': {
                                    "url": f"data:image/jpeg;base64,{image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=700
            )
            return response.choices[0].message.content
        except Exception as e:
            print(e)
            return None
    
    # Converting image to base64
    base64_image=convert_base64(image)
    
    if not base64_image:
        print("Error in image conversion, stopping analysis.")
        return None

    # Analyzing the image
    response=gpt_analysis_agent(base64_image)

    print("the response is :",response)
    return response

# Parsing the response
def parse_analysis(analysis_text):
    sections = re.split(r'#{1,4}\s', analysis_text)
    parsed_data = {}

    for section in sections:
        if section.strip():
            lines = section.strip().split('\n')
            title = lines[0].strip(':')
            content = '\n'.join(lines[1:])
            parsed_data[title] = content

    return parsed_data


def main():
    load_dotenv()
    st.title("Workspace Analysis App")

    st.write("Upload an image of your workspace for analysis...")

    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:

        # Check if the file format is supported
        file_type = uploaded_file.type
        if file_type not in ["image/jpeg", "image/png"]:
            st.error("Invalid file format. Please upload a JPG, JPEG, or PNG image.")

        else:
            try:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_column_width=True)

                if st.button("Analyze Workspace"):
                    with st.spinner("Analyzing image..."):
                        analysis = analyze_image(image)
                        
                        # Extract the analysis text from the GPT response
                        parsed_data = parse_analysis(analysis)
                        
                        # Display results using expanders
                        for title, content in parsed_data.items():
                            with st.expander(title):
                                st.markdown(content)

            except Exception as e:
                st.error(f"An error occurred while processing the image: {str(e)}")
                

if __name__ == "__main__":
    main()
