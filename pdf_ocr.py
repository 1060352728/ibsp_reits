from ollama_ocr import OCRProcessor
import os

def process_pdf_file(pdf_path, output_dir="ocr_output"):
    print(f"文档路径: {pdf_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    ocr = OCRProcessor(model_name="qwen2.5vl:7b")
    
    # Process the PDF
    result = ocr.process_image(
        image_path=pdf_path,
        format_type="markdown",
        language="zh",
        custom_prompt="将该pdf文件以markdown格式输出，保持原有的格式和结构"
    )
    
    # Save the result to a file
    filename = os.path.basename(pdf_path)
    output_filename = os.path.splitext(filename)[0] + '.md'
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"Output saved to: {output_path}")
    return result

if __name__ == "__main__":
    pdf_path = "sh/2025-07-31/华夏南京交通高速公路封闭式基础设施证券投资基金关于二〇二五年六月主要运营数据的公告.pdf"
    
    if os.path.exists(pdf_path):
        content = process_pdf_file(pdf_path)
        print("\nProcessed content:")
        print(content)