def offline_template(product_name, product_description, target_audience, marketing_objective, platforms, brand_tone):
    """Editable placeholder brief used only when Gemini is unavailable. Not AI-generated."""
    platform_list = ", ".join(platforms) if platforms else "your platforms"
    return {
        "headline": "[Edit] Introducing " + product_name,
        "tagline": "[Edit] A tagline for " + product_name + " in a " + brand_tone.lower() + " tone.",
        "product_description": product_description or "[Edit] Describe the product.",
        "captions": [
            "[Edit] Caption 1 for " + platform_list + " about " + product_name + ".",
            "[Edit] Caption 2 aimed at " + target_audience + ".",
            "[Edit] Caption 3 that supports: " + marketing_objective + ".",
        ],
        "hashtags": ["#" + product_name.replace(" ", ""), "#Edit"],
        "ctas": ["[Edit] Shop now", "[Edit] Learn more", "[Edit] Try it today"],
        "visual_concept": "[Edit] Describe the visual for " + product_name + ".",
    }
