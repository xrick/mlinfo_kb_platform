from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

class ContentSplitter:
    def __init__(self, chunk_size=1000, chunk_overlap=100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.default_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        self.md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ])

    def split_text(self, text: str, file_type: str = 'txt'):
        """
        根據檔案類型分割文本
        :param text: 要分割的文本
        :param file_type: 'txt' 或 'md'
        :return: 分割後的文本區塊列表
        """
        if file_type.lower() == 'md':
            # 對於 Markdown，先按標題分割，再對長段落進行遞迴分割
            md_chunks = self.md_splitter.split_text(text)
            final_chunks = []
            for chunk in md_chunks:
                if len(chunk.page_content) > self.chunk_size:
                    sub_chunks = self.default_splitter.create_documents([chunk.page_content])
                    # 將元數據加回去
                    for sub_chunk in sub_chunks:
                        sub_chunk.metadata.update(chunk.metadata)
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(chunk)
            return final_chunks
        else:
            return self.default_splitter.create_documents([text])