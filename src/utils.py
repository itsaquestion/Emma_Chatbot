import re
import xml.etree.ElementTree as ET
def extract_letters(string):
    letters = []
    for char in string:
        if "a" <= char <= "z" or "A" <= char <= "Z":
            letters.append(char)
    return "".join(letters)


# def get_final_assessment(text) -> str:
#     """
#     从多行字符串中提取Final Assessment的结果。

#     参数:
#     text (str) - 包含Final Assessment信息的多行字符串

#     返回:
#     str - "Yes"或"No"
#     """
    
#     result = text.split(":")
    
#     if len(result) > 0:
#         result = result[-1].strip()

#     return result

def format_conversation_history(history):
    formatted_text = ""
    for entry in history:
        role = entry.get("role", "Unknown")
        content = entry.get("content", "")
        formatted_text += f"{role.capitalize()}:\n{content}\n\n"
    return formatted_text.strip()


def extract_final_score(xml_string):
    try:
        # Parse the XML string
        root = ET.fromstring(xml_string)
        
        # Find the overall_assessment element
        overall_assessment = root.find('.//overall_assessment')
        
        if overall_assessment is not None:
            # Find the score element within overall_assessment
            score_element = overall_assessment.find('score')
            
            if score_element is not None:
                # Extract the score value and convert it to an integer
                return float(score_element.text)
    
    except ET.ParseError:
        print("Error: Invalid XML format")
    except ValueError:
        print("Error: Score is not a valid integer")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    # Return None if any error occurs or if the score is not found
    return None

def extract_idiomatic_rewrite(xml_string):
    try:
        # Parse the XML string
        root = ET.fromstring(xml_string)
        
        # Find the overall_assessment element
        overall_assessment = root.find('.//overall_assessment')
        
        if overall_assessment is not None:
            # Find the score element within overall_assessment
            score_element = overall_assessment.find('idiomatic_rewrite')
            
            if score_element is not None:
                # Extract the score value and convert it to an integer
                return score_element.text
                
    except ET.ParseError:
        print("Error: Invalid XML format")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    # Return None if any error occurs or if the score is not found
    return None

def xml_to_friendly_string(xml_string):
    def process_element(element, depth=0):
        result = []
        indent = "" * depth
        tag = element.tag
        
        # Check if this is a leaf node (has no child elements)
        if len(element) == 0:
            # If it's a leaf node, put content on the same line
            content = element.text.strip() if element.text else ""
            result.append(f"{indent}[**{tag}**]: {content}")
        else:
            # If it's not a leaf node, keep the original format
            result.append(f"{indent}[**{tag}**]: ")
            if element.text and element.text.strip():
                result.append(f"{indent}  {element.text.strip()}")
            
            for child in element:
                result.extend(process_element(child, depth + 1))
        
        return result

    try:
        root = ET.fromstring(xml_string)
        friendly_lines = process_element(root)
        return "\n".join(friendly_lines)
    except ET.ParseError:
        return "Error: Invalid XML format"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
    
    
if __name__ == "__main__":
    xml_string = """<gc>
<analysis>
<intended_meaning>The user is inquiring about my name.</intended_meaning>
<sentence_analysis>
<original>Hi! What's your name?</original>
<corrected>No corrections needed.</corrected>
<improved>No improvements needed.</improved>
<score>5</score>
<explanation>This sentence is already grammatically correct, clear, and natural. It is an idiomatic expression commonly used in English.</explanation>
</sentence_analysis>
</analysis>
<overall_assessment>
  <score>5</score>
  <explanation>The user's input is already grammatically correct, clear, and natural. No improvements are needed.</explanation>
  <exemplar_paragraph>Hi! What's your name?</exemplar_paragraph>
</overall_assessment>
</gc>"""

    score = extract_final_score(xml_string)
    if score is not None:
        print(f"Final Score: {score}")
    else:
        print("Failed to extract final score.")
        
    print(xml_to_friendly_string(xml_string))