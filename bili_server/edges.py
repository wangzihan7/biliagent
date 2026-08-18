class EdgeGraph:
    def __init__(self):

        ...

    def decide_to_generate(self, state):
        """
        根据过滤后的文档与输入问题的相关性确定是生成答案还是重新生成问题。
        """
        print("---进入检索文档与问题相关性判断---")

        filtered_documents = state["documents"]

        if not filtered_documents:
            print("---决策：所有检索到的文档均与问题无关，转换查询---")
            return "transform_query"
        else:
            print("---决策：生成最终响应---")
            return "generate"

