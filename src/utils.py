import re
def extract_letters(string):
    letters = []
    for char in string:
        if "a" <= char <= "z" or "A" <= char <= "Z":
            letters.append(char)
    return "".join(letters)


def get_final_assessment(text) -> str:
    """
    从多行字符串中提取Final Assessment的结果。

    参数:
    text (str) - 包含Final Assessment信息的多行字符串

    返回:
    str - "Yes"或"No"
    """
    
    result = text.split(":")
    
    if len(result) > 0:
        result = result[-1].strip()

    return result

