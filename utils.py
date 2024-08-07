import re
def extract_letters(string):
    letters = []
    for char in string:
        if "a" <= char <= "z" or "A" <= char <= "Z":
            letters.append(char)
    return "".join(letters)


def get_final_assessment(text):
    """
    从多行字符串中提取Final Assessment的结果。

    参数:
    text (str) - 包含Final Assessment信息的多行字符串

    返回:
    str - "Yes"或"No"
    """
    pattern = r"Final Assessment: (Yes|No)"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return None

