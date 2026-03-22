from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    def __init__(self, model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, items: list[dict], top_n: int = 10):
        if not items:
            return []

        pairs = [(query, item['text']) for item in items]
        scores = self.model.predict(pairs)
        # rescored = list(zip(scores, items))
        # rescored.sort(key=lambda x: x[0], reverse=True)

        # return [item for _, item in rescored[:top_n]]

        rescored_items = []

        for score, item in zip(scores, items):
            new_item = item.copy()
            new_item["rerank_score"] = float(score)  # 👈 thêm score mới
            rescored_items.append(new_item)

        rescored_items.sort(key=lambda x: x["rerank_score"], reverse=True)

        return rescored_items[:top_n]