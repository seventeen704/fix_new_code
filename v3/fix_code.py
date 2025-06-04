import re

def replace_ctype_usages(code):
    # 替换 _ctype_b、_ctype_tolower、_ctype_toupper 等旧式宏访问为标准 ctype.h 宏。

    # 1a: *(unsigned __int16 *)(expr + _ctype_b) >> N & 1
    def replace_ctype_b(match):
        expr = match.group(1)
        bit = match.group(2)
        mapping = {
            '11': f'isalpha({expr})',
            '5':  f'isspace({expr})',
            '4':  f'isxdigit({expr})',
            '3':  f'isdigit({expr})',
            '1':  f'islower({expr})'
        }
        return mapping.get(bit, f'/* unknown _ctype_b bit {bit} */ 0')

    code = re.sub(
        r'\(\*\(unsigned __int16\s*\*\)\s*\(\s*(.*?)\s*\+\s*_ctype_b\s*\)\s*>>\s*(\d+)\)\s*&\s*1',
        replace_ctype_b,
        code
    )

    # 1b: (*(_WORD *)(expr + _ctype_b) & 1)
    code = re.sub(
        r'\(\*\(_WORD\s*\*\)\s*\(\s*(.*?)\s*\+\s*_ctype_b\s*\)\s*&\s*1\s*\)',
        lambda m: f'islower({m.group(1)})',
        code
    )

    # 2. 替换 _ctype_tolower
    code = re.sub(
        r'\*\(__?int(8|16|32)?\s*\*\)\s*\(\s*2\s*\*\s*(\*?\w+)\s*\+\s*_ctype_tolower\s*\)',
        r'tolower(\2)',
        code
    )
    code = re.sub(
        r'\*\(_WORD\s*\*\)\s*\(\s*(.*?)\s*\+\s*_ctype_tolower\s*\)',
        r'tolower(\1)',
        code
    )

    # 3. 替换 _ctype_toupper
    code = re.sub(
        r'\*\(__?int(8|16|32)?\s*\*\)\s*\(\s*2\s*\*\s*(\*?\w+)\s*\+\s*_ctype_toupper\s*\)',
        r'toupper(\2)',
        code
    )
    code = re.sub(
        r'\*\(unsigned __int8\s*\*\)\s*\(\s*2\s*\*\s*(\*?\w+)\s*\+\s*_ctype_toupper\s*\)',
        r'toupper(\1)',
        code
    )
    code = re.sub(
        r'\*\(_WORD\s*\*\)\s*\(\s*(.*?)\s*\+\s*_ctype_toupper\s*\)',
        r'toupper(\1)',
        code
    )

    # 4. 添加 #include <ctype.h>
    if '#include <ctype.h>' not in code:
        code = '#include <ctype.h>\n' + code

    return code


def remove_const(code):
    return re.sub(r'\bconst\b', '', code)



def replace_free(code):
    return re.sub(r'\bfree\s*\(([^;]*)\);', r'free2(\1);', code)


def fix_fclose_calls(code):
    # 将 fclose(x, y) 替换为 fclose(x)"""
    return re.sub(r'\bfclose\s*\(\s*([^,]+?)\s*,\s*[^)]+\)', r'fclose(\1)', code)


def fix_memmove_calls(code):
    # 将 memmove(x) 替换为 memmove(x, x, 0)"""
    return re.sub(r'\bmemmove\s*\(\s*([^\),;]+)\s*\)', r'memmove(\1, \1, 0)', code)


def fix_sslEncodeResponse_calls(code):
    # 截断 sslEncodeResponse(...) 调用，只保留前 3 个参数"""
    def truncate_args(match):
        args = [arg.strip() for arg in match.group(1).split(',')]
        return f"sslEncodeResponse({', '.join(args[:3])})"
    return re.sub(r'\bsslEncodeResponse\s*\(([^)]*)\)', truncate_args, code)


def fix_strchr_calls(code):
    # 修复 strchr() 调用缺少参数的问题"""
    return re.sub(r'\bstrchr\s*\(\s*\)', r'strchr(NULL, 0)', code)


def replace_pointer_audiovol(code):
    # 将 *audiovol_select 替换为 audiovol_select"""
    return re.sub(r'\*\s*(audiovol_select)\b', r'\1', code)


def remove_noreturn(code):
    return re.sub(r'\b__noreturn\b', '', code)


def comment_all_asm_blocks(code):
    # 注释掉所有包含 __asm { ... } 的单行汇编指令
    return re.sub(r'^(.*__asm\s*\{[^}]*\})', r'// \1', code, flags=re.MULTILINE)


def simplify_sub_408D10_all(code):
    # 先处理声明后换行大括号的情况（复杂指针或简单函数名）
    pattern_decl_with_brace = re.compile(
        r'\bint\s+(\(\*\(*\**sub_408D10\s*\([^)]*\)\)*|sub_408D10)\s*\([^)]*\)\s*;\s*\s*\{',
        re.DOTALL
    )
    code = pattern_decl_with_brace.sub('int *sub_408D10() {', code)

    # 单独处理简单函数名带参数声明（无函数体）
    code = re.sub(r'\bint\s+[^;{]*?\bsub_408D10\b[^;{]*?;', 'int *sub_408D10();', code)
    return code


def fix_code(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        code = f.read()

    code = replace_ctype_usages(code)
    code = remove_const(code)
    code = replace_free(code)
    code = fix_fclose_calls(code)
    code = fix_memmove_calls(code)
    code = fix_sslEncodeResponse_calls(code)
    code = fix_strchr_calls(code)
    code = replace_pointer_audiovol(code)
    code = remove_noreturn(code)
    code = comment_all_asm_blocks(code)
    code = simplify_sub_408D10_all(code)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)


fix_code("new.c", "new_fix.c")
