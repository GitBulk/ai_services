# app/services/ranking/heuristic_reranker.py

class HeuristicReranker:

    def rerank(self, query: str, items: list[dict], top_n: int = 10):
        query_terms = set(query.lower().split())

        rescored = []

        for item in items:
            base_score = item.get("score", 0.0)
            text = item.get("text", "").lower()

            # 1. keyword overlap
            text_terms = set(text.split())
            overlap = len(query_terms & text_terms)
            keyword_boost = overlap * 0.1

            # 2. length normalization (tránh text quá ngắn)
            length = len(text)
            length_score = min(length / 200, 1.0)

            # 3. simple final score
            final_score = base_score + keyword_boost + length_score

            rescored.append((final_score, item))

        rescored.sort(key=lambda x: x[0], reverse=True)

        # chỉ trả item (giữ nguyên format dict)
        return [item for _, item in rescored[:top_n]]