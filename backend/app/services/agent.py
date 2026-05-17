from decimal import Decimal

from app.models import Post, Product


class AgentService:
    def generate_copy(self, post: Post) -> dict:
        products = sorted(post.products, key=lambda item: item.sort_order)
        product_names = [item.product_name for item in products]
        title_subject = "、".join(product_names[:3]) if product_names else "Byt 产品"
        copy_style = self._style_text(post.copy_custom_prompt)
        image_style = self._style_text(post.image_custom_prompt)

        title_options = self._title_options(title_subject, copy_style)
        content_blocks = [
            self._opening(copy_style),
            self._style_note("文案风格要求", copy_style),
        ]
        product_copy_results = []

        for index, product in enumerate(products, start=1):
            price = f"{product.price} 元" if product.price is not None else "价格未记录"
            summary = self._summarize_product(product)
            content_blocks.append(
                f"{index}. {product.product_name}，{price}。{product.user_impression}。我的判断是：{summary}"
            )
            product_copy_results.append(
                {
                    "product_id": product.id,
                    "agent_summary": summary,
                    "agent_recommendation": self._recommendation(product.user_impression),
                    "pros": self._pros(product.user_impression),
                    "cons": self._cons(product.user_impression),
                    "suitable_for": "想看真实体验、愿意先小量尝试的人",
                    "not_suitable_for": "需要强确定性推荐或只追求最低价的人",
                    "copy_style_instruction": copy_style,
                }
            )

        content_blocks.append("如果你也在看 Byt 相关产品，可以先按自己的使用场景选，不建议只看包装或跟风囤。")

        return {
            "selected_title": title_options[0],
            "title_options": title_options,
            "content": "\n\n".join([block for block in content_blocks if block]),
            "cover_text": self._cover_text(copy_style),
            "tags": ["Byt测评", "真实测评", "小红书测评", "产品体验", "避雷种草"],
            "comment_guide": "你还想看哪款 Byt 产品？评论区告诉我，下期继续测。",
            "recommendation_level": self._overall_recommendation(products),
            "product_copy_results": product_copy_results,
            "image_order_suggestion": self._image_plan(image_style),
        }

    def analyze_metrics(self, post: Post, metrics: dict) -> dict:
        interaction_rate = metrics["interaction_rate"]
        collect_rate = metrics["collect_rate"]
        follower_rate = metrics["follower_rate"]
        strengths = []
        risks = []

        if interaction_rate >= Decimal("0.08"):
            strengths.append("互动率较好，标题和测评角度能带动读者反馈。")
        else:
            risks.append("互动率偏低，前 3 行正文和评论引导需要更直接。")

        if collect_rate >= Decimal("0.025"):
            strengths.append("收藏率不错，内容具备一定参考价值。")
        else:
            risks.append("收藏率不高，可以增加明确的购买结论和对比维度。")

        if follower_rate < Decimal("0.005"):
            risks.append("转粉率偏低，账号记忆点和系列化栏目需要加强。")

        title = post.selected_title or "未命名帖子"
        result = {
            "summary": f"《{title}》本次浏览 {metrics['views']}，互动率 {float(interaction_rate) * 100:.2f}%，收藏率 {float(collect_rate) * 100:.2f}%。",
            "strengths": strengths or ["本次数据没有明显强项，建议先优化标题和封面信息密度。"],
            "risks": risks or ["核心数据稳定，可以继续沿用这类真实测评结构。"],
            "next_topics": ["同类产品横评", "价格差异明显的 Byt 产品", "带争议点的真实避雷测评"],
            "title_advice": "标题保留真实口吻，同时补充品类和结论，例如“哪些能冲，哪些不用囤”。",
            "cover_advice": "封面文案控制在两行，直接写测评对象和判断，不要堆太多修饰。",
            "copy_style_instruction": self._style_text(post.copy_custom_prompt),
            "image_style_instruction": self._style_text(post.image_custom_prompt),
        }
        result["text"] = "\n".join(
            [
                result["summary"],
                "表现好的地方：" + "；".join(result["strengths"]),
                "需要调整：" + "；".join(result["risks"]),
                "下一期建议：" + "、".join(result["next_topics"]),
            ]
        )
        return result

    def _style_text(self, value: str | None) -> str:
        return value.strip() if value and value.strip() else ""

    def _title_options(self, title_subject: str, copy_style: str) -> list[str]:
        if copy_style:
            return [
                f"按这个风格测 Byt：{title_subject}值不值得买",
                f"{title_subject}真实体验，我按自己的口吻说清楚",
                f"这期 Byt 测评按你的风格来：有优点也有保留",
                f"{title_subject}横评：哪些适合继续买",
                f"不是广告，{title_subject}我只写实际感受",
            ]
        return [
            f"Byt真实测评：{title_subject}值不值得买",
            "这期Byt测完，我把真实感受写清楚了",
            f"不是广告，{title_subject}我只说体验",
            "Byt这几款产品，有惊喜也有小踩雷",
            f"{title_subject}横评：哪些适合继续买",
        ]

    def _opening(self, copy_style: str) -> str:
        if copy_style:
            return f"这期按我设定的表达风格来写：{copy_style}。体验部分仍然只基于实际输入，不额外编造。"
        return "这期记录的是实际体验，不做夸张推荐。整体结论先说：有些值得尝试，也有些只适合按需买。"

    def _style_note(self, label: str, style: str) -> str:
        if not style:
            return ""
        return f"{label}：{style}"

    def _cover_text(self, copy_style: str) -> str:
        if "避雷" in copy_style:
            return "Byt真实避雷\n哪些不用囤"
        if "温柔" in copy_style or "克制" in copy_style:
            return "Byt真实体验\n适合按需买"
        return "Byt真实测评\n值不值得买"

    def _image_plan(self, image_style: str) -> str:
        if image_style:
            return f"图片处理需遵循用户自定义风格：{image_style}。第一张优先选择主体清晰、留白足够的图片作为封面，后续按正文产品顺序排列。"
        return "建议第一张使用主体清晰、背景干净的图片作为封面，后续按正文测评顺序排列。"

    def _summarize_product(self, product: Product) -> str:
        impression = product.user_impression.strip()
        if len(impression) <= 36:
            return impression
        return impression[:36].rstrip("，。,. ") + "。"

    def _recommendation(self, impression: str) -> str:
        negative_words = ["踩雷", "难吃", "不好", "一般", "腻", "贵", "失望"]
        positive_words = ["好吃", "清爽", "喜欢", "不错", "划算", "惊喜"]
        negative = any(word in impression for word in negative_words)
        positive = any(word in impression for word in positive_words)
        if positive and not negative:
            return "轻种草"
        if negative and not positive:
            return "谨慎"
        return "中立"

    def _pros(self, impression: str) -> list[str]:
        pros = []
        for word in ["好看", "清爽", "好吃", "方便", "划算", "香", "口感"]:
            if word in impression:
                pros.append(word)
        return pros or ["体验信息真实"]

    def _cons(self, impression: str) -> list[str]:
        cons = []
        for word in ["贵", "腻", "甜", "一般", "不好", "踩雷"]:
            if word in impression:
                cons.append(word)
        return cons or ["需要更多数据验证"]

    def _overall_recommendation(self, products: list[Product]) -> str:
        recommendations = [self._recommendation(item.user_impression) for item in products]
        if recommendations.count("轻种草") > recommendations.count("谨慎"):
            return "中立偏种草"
        if recommendations.count("谨慎") > recommendations.count("轻种草"):
            return "中立偏避雷"
        return "中立"


agent_service = AgentService()

