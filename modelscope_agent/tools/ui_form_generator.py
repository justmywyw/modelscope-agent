from http import HTTPStatus

from dashscope import Generation
from modelscope_agent.tools.tool import Tool, ToolSchema
from pydantic import ValidationError

form_typescript = """
export type FormResponse = {
    formItems: (InputFormItem | RadioFormItem | CheckboxFormItem | SelectFormItem | UnknownFormItem)[]
}

/**
 * 表单项控件类型
 */
export type FormItemType = 'input' | 'radio' | 'checkbox' | 'select';

/**
 * 未知的表单控件
 */
export interface UnknownFormItem {
    itemType: 'unknown',
    /**
     * 未知的表单控件的描述
     */
    desc: string;
}

export interface FormItem {
    /**
     * 表单控件类型
     */
    itemType: FormItemType;
    /**
     * 表单数据模型的key名称
     */
    modelKeyName: string;
    /**
     * 表单数据模型的value的类型
     */
    modelValueType: 'string' | 'number' | 'Array<string>' | 'Array<number>';
    /**
     * 是否必填
     */
    required: boolean;
    /**
     * 表单的标签
     */
    label: string;
}

export interface FormItem {
    /**
     * 表单控件类型
     */
    itemType: FormItemType;
    /**
     * 表单数据模型的key名称
     */
    modelKeyName: string;
    /**
     * 表单数据模型的value的类型
     */
    modelValueType: 'string' | 'number' | 'Array<string>' | 'Array<number>';
    /**
     * 是否必填
     */
    required: boolean;
}

/**
 * 表单控件：Input 输入框
 * 通过鼠标或键盘输入字符
 */
export interface InputFormItem extends FormItem {
    itemType: 'input';
    modelValueType: 'string';
    /**
     * 表单校验：字符串最小长度
     */
    minLength: number | null;
    /**
     * 表单校验：字符串最大长度
     */
    maxLength: number | null;
    /**
     * 表单校验：字符串需要符合的正则表达式
     */
    pattern: string | null;
    /**
     * 默认值
     */
    default: string | null;
}

/**
 * 表单备选项
 */
export interface FormItemOption {
    /**
     * 选项标签
     */
    label: string;
    /**
     * 选项值
     */
    value: string | number;
}

/**
 * 表单控件：Radio 单选框
 * 在一组备选项中进行单选
 */
export interface RadioFormItem extends FormItem {
    itemType: 'radio';
    modelValueType: 'string' | 'number';
    /**
     * 默认值
     */
    default: string | number | null;
    /**
     * 备选选项
     */
    options: Array<FormItemOption>
}

/**
 * 表单控件：Checkbox  多选框
 * 在一组备选项中进行多选。
 */
export interface CheckboxFormItem extends FormItem {
    itemType: 'checkbox';
    modelValueType: 'Array<string>' | 'Array<number>';
    /**
     * 默认值
     */
    default: string | number | null;
    /**
     * 备选选项
     */
    options: Array<FormItemOption>
}

/**
 * 表单控件：Select 选择器
 * 当选项过多时，使用下拉菜单展示并选择内容。
 */
export interface SelectFormItem extends FormItem {
    itemType: 'select';
    /**
     * 单选为string
     * 多选为Array<string>
     */
    modelValueType: 'string' | 'Array<string>';
    /**
     * 是否多选
     */
    multiple: boolean;
    /**
     * 最少需要选几项
     */
    minItems: number | null;
    /**
     * 最多需要选几项
     */
    maxItems: number | null;
    /**
     * 备选选项
     */
    options: Array<FormItemOption>
}
"""


class UiFormGenerator(Tool):
    description = '一个表单生成器，可以根据用户的展示需求在对话框中展示输入框、可选项等内容，将文字描述转换成对应可渲染的表单'
    name = 'ui_form_generator'
    parameters: list = [{
        'name': 'input',
        'description': """用户输入的展示需求""",
        'required': True
    }]

    def __init__(self, cfg={}):
        super().__init__(cfg)
        try:
            all_param = {
                'name': self.name,
                'description': self.description,
                'parameters': self.parameters
            }
            self.tool_schema = ToolSchema(**all_param)
        except ValidationError:
            raise ValueError(f'Error when parsing parameters of {self.name}')

        self._str = self.tool_schema.model_dump_json()
        self._function = self.parse_pydantic_model_to_openai_function(
            all_param)

    def __call__(self, *args, **kwargs):
        input = kwargs['input']
        system_prompt = f"""
为我将用户输入翻译成以下的 JSON 对象，根据以下的 TypeScript 声明:
```
{form_typescript}
```

输出的内容不需要用代码块包裹，中间为完整的 json 对象内容，不需要输出其他任何内容
"""
        response = Generation.call(
            model='qwen-max',
            messages=[{
                'role': 'system',
                'content': system_prompt
            }, {
                'role': 'user',
                'content': input
            }],
            result_format='message',
            temperature=1.0,
            repetition_penalty=1.0)
        if response.status_code == HTTPStatus.OK:
            ret = response.output.choices[0].message.content
            return ret


if __name__ == '__main__':
    tool = UiFormGenerator()
    res = tool(input='给出 东、西、南、北 四个选项让用户选择')
    print(res)
