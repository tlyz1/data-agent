import asyncio
from typing import Optional

import httpx

from app.conf.app_config import app_config, EmbeddingConfig


class TeiEmbeddingsClient:
    """
    本地 text-embeddings-inference(TEI)服务的轻量客户端。

    为什么不直接用 langchain_huggingface.HuggingFaceEndpointEmbeddings：
    该类的 model 参数只接受 HuggingFace 仓库 id（传 URL 会直接报错），
    并且它在构造时会把内部 client 固定成官方 Inference API，无法指向本地 TEI。
    这里直接调用 TEI 的 /embed 接口，保持与 langchain Embeddings 一致的调用方式：
    embed_query / aembed_query         -> list[float]
    embed_documents / aembed_documents -> list[list[float]]
    """

    def __init__(self, base_url: str, model: Optional[str] = None, timeout: float = 60.0, batch_size: int = 32):
        # TEI 单次请求的条数上限（max_client_batch_size）
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.batch_size = batch_size

    def _payload(self, texts: list[str]) -> dict:
        # truncate=True 避免超过 max_input_length 时直接报 413
        return {"inputs": texts, "truncate": True}

    @staticmethod
    def _parse(response: httpx.Response) -> list[list[float]]:
        # 请求失败时抛出 httpx.HTTPStatusError，便于上层定位问题
        response.raise_for_status()
        vectors = response.json()
        # TEI 正常返回 [[...],[...]]，这里兼容单条返回一维数组的情况
        if vectors and not isinstance(vectors[0], list):
            vectors = [vectors]
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        同步批量向量化
        :param texts:
        :return: [[0.1,0.2,...],[...]]
        """
        embeddings: list[list[float]] = []
        with httpx.Client(timeout=self.timeout) as client:
            for i in range(0, len(texts), self.batch_size):
                # 换行会影响向量质量，先替换掉
                batch_texts = [text.replace("\n", " ") for text in texts[i:i + self.batch_size]]
                response = client.post(f"{self.base_url}/embed", json=self._payload(batch_texts))
                embeddings.extend(self._parse(response))
        return embeddings

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        异步批量向量化
        :param texts:
        :return: [[0.1,0.2,...],[...]]
        """
        embeddings: list[list[float]] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for i in range(0, len(texts), self.batch_size):
                # 换行会影响向量质量，先替换掉
                batch_texts = [text.replace("\n", " ") for text in texts[i:i + self.batch_size]]
                response = await client.post(f"{self.base_url}/embed", json=self._payload(batch_texts))
                embeddings.extend(self._parse(response))
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """
        同步单条向量化（对齐 langchain Embeddings 接口）
        :param text:
        :return: [0.1,0.2,...]
        """
        # TEI 的 /embed 接口同样支持单条文本输入，这里复用批量逻辑取第一条
        return self.embed_documents([text])[0]

    async def aembed_query(self, text: str) -> list[float]:
        """
        异步单条向量化（对齐 langchain Embeddings 接口）
        :param text:
        :return: [0.1,0.2,...]
        """
        # TEI 的 /embed 接口同样支持单条文本输入，这里复用批量逻辑取第一条
        return (await self.aembed_documents([text]))[0]


class EmbeddingClientManager:

    def __init__(self,config:EmbeddingConfig):
        self.client: Optional[TeiEmbeddingsClient] = None
        self.config = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = TeiEmbeddingsClient(
            base_url=self._get_url(),
            model=self.config.model,
        )


embedding_client_manager =EmbeddingClientManager(app_config.embedding)


if __name__ == '__main__':
    # 初始化对象
    embedding_client_manager.init()

    async def test():
        # 获取对象
        client = embedding_client_manager.client

        # 定义文本
        text = "你好，我爱中国"
        # 单条向量化
        result=await client.aembed_query(text)

        print(type(result))
        print(len(result))
        print(result[:5])

    asyncio.run(test())











