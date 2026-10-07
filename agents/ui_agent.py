import re
import time
from typing import Dict, Any, List, Optional
from data.database import get_database

QUANTITY_WORDS = {
    "one": 1, "a": 1, "an": 1, "single": 1,
    "two": 2, "pair": 2, "couple": 2, "double": 2,
    "three": 3, "triple": 3,
    "four": 4,
    "five": 5,
    "six": 6, "half-dozen": 6, "half dozen": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "twelve": 12, "dozen": 12
}

TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90
}

ONES = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19
}

def extract_cart_quantity(text: str) -> int:
    """Extracts explicit digits or natural language quantity words."""
    # 1. Check for explicit digits
    digit_match = re.search(r'\b(\d+)\s*(?:bottles?|items?|units?|packs?|jars?|pieces?|pcs|of)?\b', text, re.IGNORECASE)
    if digit_match:
        try:
            qty = int(digit_match.group(1))
            if 1 <= qty <= 100:
                return qty
        except ValueError:
            pass

    q_lower = text.lower()
    words = re.findall(r'[a-z]+', q_lower)

    if "couple" in words or "pair" in words:
        return 2
    if "dozen" in words:
        return 12

    for idx, w in enumerate(words):
        if w in QUANTITY_WORDS and w not in ["a", "an"]:
            if idx == 0 or (idx + 1 < len(words) and words[idx+1] in ["items", "item", "bottles", "bottle", "units", "unit", "packs", "pack", "jars", "jar", "of", "pieces", "pcs"]):
                return QUANTITY_WORDS[w]
            if idx > 0 and words[idx-1] in ["add", "buy", "order", "get", "put", "want"]:
                return QUANTITY_WORDS[w]
            if QUANTITY_WORDS[w] >= 2:
                return QUANTITY_WORDS[w]

    return 1

def parse_spoken_number(text: str) -> Optional[float]:
    """Parses digits or spoken compound number words from natural voice/text input."""
    # 1. Prioritize explicit dollar amounts: $29.99, $30, for $25.50
    dollar_match = re.search(r'\$\s*(\d+(?:\.\d{1,2})?)', text)
    if dollar_match:
        try:
            return float(dollar_match.group(1))
        except ValueError:
            pass

    # 2. Check for "price ... 29.99" or "for 29.99 dollars"
    price_match = re.search(r'(?:price|cost|for|under|below|at)\s+(?:is\s+|of\s+|:\s*)?\$?\s*(\d+(?:\.\d{1,2})?)(?!\s*[%|ml|mg|oz|g|kg])', text, re.IGNORECASE)
    if price_match:
        try:
            return float(price_match.group(1))
        except ValueError:
            pass

    # 3. Check for standalone decimal numbers (e.g. 29.99) not followed by %/units
    decimal_match = re.search(r'\b(\d+\.\d{1,2})\b(?!\s*[%|ml|mg|oz|g|kg])', text)
    if decimal_match:
        try:
            return float(decimal_match.group(1))
        except ValueError:
            pass

    # 4. Check for standalone integers not followed by %/units
    int_match = re.search(r'\b(\d+)\b(?!\s*[%|ml|mg|oz|g|kg])', text)
    if int_match:
        try:
            return float(int_match.group(1))
        except ValueError:
            pass

    q_clean = re.sub(r'[^a-z\s\-]', ' ', text.lower())
    words = q_clean.split()

    for i in range(len(words)):
        w = words[i].replace("-", " ")
        parts = w.split()
        if len(parts) == 2 and parts[0] in TENS and parts[1] in ONES:
            return float(TENS[parts[0]] + ONES[parts[1]])

        if words[i] in TENS:
            if i + 1 < len(words) and words[i + 1] in ONES:
                return float(TENS[words[i]] + ONES[words[i + 1]])
            return float(TENS[words[i]])

        if words[i] in ONES:
            return float(ONES[words[i]])

    return None


class UIAutomationAgent:
    """
    UI Action & Automation Agent for FolliCare Botanical Hair Cosmetics:
    Translates user natural speech/text instructions into declarative UI Action Commands
    with robust voice normalization, color transitions, and database product matching.
    """
    def __init__(self):
        self.agent_name = "UI Automation & Action Agent"
        self.db = get_database()

    def plan_and_execute(self, query: str, context: Optional[str] = "") -> Dict[str, Any]:
        start_time = time.time()
        q_lower = query.lower()
        commands: List[Dict[str, Any]] = []
        action_descriptions: List[str] = []

        # 1. THEME AUTOMATION (Smart Transition & Color Hierarchy)
        theme_map = {
            "ruby-red": ["ruby", "red", "crimson", "scarlet", "cherry", "maroon", "burgundy", "vermilion"],
            "ocean-blue": ["ocean", "blue", "sapphire", "cyan", "azure", "navy", "marine", "cobalt", "aqua", "water", "teal"],
            "botanical-emerald": ["emerald", "botanical", "green", "herbal", "nature", "forest", "sage", "mint", "olive"],
            "rose-luxury": ["rose", "pink", "luxury", "blush", "gold", "rose gold", "coral", "magenta"],
            "lavender-clean": ["lavender", "purple", "violet", "clean", "dermatologist", "lilac", "plum", "amethyst"],
            "amber-noir": ["dark", "amber", "noir", "night", "dark mode", "midnight", "black", "honey", "charcoal"],
            "light-minimal": ["light", "white", "minimal", "light mode", "clean minimal", "bright"]
        }

        theme_matched = None
        # Check transition patterns first (e.g. "change green to red", "switch from emerald into ruby red", "to red color")
        target_color_match = re.search(r'(?:to|into|become|make it|switch to|change to)\s+([a-z\s\-]+)', q_lower)
        if target_color_match:
            target_phrase = target_color_match.group(1).strip()
            for theme_key, keywords in theme_map.items():
                if any(kw in target_phrase.split() or kw == target_phrase for kw in keywords):
                    theme_matched = theme_key
                    break

        # If not matched via transition, match directly by keyword in query
        if not theme_matched:
            for theme_key, keywords in theme_map.items():
                if any(kw in q_lower.split() or re.search(rf'\b{re.escape(kw)}\b', q_lower) for kw in keywords):
                    theme_matched = theme_key
                    break

        if theme_matched and any(w in q_lower for w in ["theme", "mode", "switch", "change", "set", "style", "look", "background", "color", "palette", "aesthetic"]):
            commands.append({
                "action": "SET_THEME",
                "payload": {"theme": theme_matched}
            })
            action_descriptions.append(f"Switched storefront visual aesthetic to '{theme_matched}'.")

        # 2. PROMOTIONAL BANNER AUTOMATION
        if any(w in q_lower for w in ["banner", "announcement", "flash sale", "promo bar", "announcement bar", "special offer", "discount banner"]):
            pct_num = parse_spoken_number(query) or 25
            pct = str(int(pct_num)) if pct_num else "25"

            code_match = re.search(r"code\s+([A-Z0-9_\-]+)", query, re.IGNORECASE)
            coupon_code = code_match.group(1).upper() if code_match else f"GROWTH{pct}"

            bg_color = "linear-gradient(90deg, #059669, #10b981)"
            if "rose" in q_lower or "pink" in q_lower:
                bg_color = "linear-gradient(90deg, #e11d48, #f43f5e)"
            elif "lavender" in q_lower or "purple" in q_lower:
                bg_color = "linear-gradient(90deg, #7c3aed, #a855f7)"
            elif "gold" in q_lower or "amber" in q_lower:
                bg_color = "linear-gradient(90deg, #d97706, #f59e0b)"
            elif "blue" in q_lower or "ocean" in q_lower:
                bg_color = "linear-gradient(90deg, #0284c7, #38bdf8)"
            elif "red" in q_lower or "ruby" in q_lower:
                bg_color = "linear-gradient(90deg, #be123c, #e11d48)"

            banner_text = f"🌿 CLINICAL HAIR WELLNESS: Enjoy {pct}% OFF Scalp & Bond Treatments! Use Code '{coupon_code}'."
            if "free shipping" in q_lower:
                banner_text = "🚚 Free Eco-Express Shipping on all Hair Cosmetics orders over $40 today!"

            commands.append({
                "action": "SET_BANNER",
                "payload": {
                    "text": banner_text,
                    "badge": f"{pct}% OFF" if "free shipping" not in q_lower else "FREE SHIP",
                    "bgColor": bg_color,
                    "coupon": coupon_code,
                    "hasCountdown": True,
                    "timerMinutes": 30
                }
            })
            action_descriptions.append(f"Deployed promotional announcement banner with code '{coupon_code}'.")

        # 3. HERO CAMPAIGN AUTOMATION
        if any(w in q_lower for w in ["hero", "headline", "campaign title", "hero title", "main header", "banner title"]):
            extracted_title = None
            title_quote = re.search(r'["\']([^"\']+)["\']', query)
            if title_quote:
                extracted_title = title_quote.group(1)
            elif " to " in q_lower:
                parts = query.split(" to ", 1)
                if len(parts) > 1:
                    extracted_title = parts[1].strip().strip('"').strip("'")

            hero_title = extracted_title or "Target Hair Fall & Density at the Follicle Root"
            hero_subtitle = "Dermatologist-developed trichological serums, biomimetic peptide masks, and herbal hair elixirs."

            if "growth" in q_lower or "thinning" in q_lower or "density" in q_lower:
                hero_subtitle = "Clinically proven botanical solutions that increase anagen hair density by up to 94%."
            elif "bond" in q_lower or "damage" in q_lower or "peptide" in q_lower:
                hero_subtitle = "Biomimetic oligopeptide formulas that reconnect broken disulfide keratin bonds in 4 minutes."

            commands.append({
                "action": "UPDATE_HERO",
                "payload": {
                    "title": hero_title,
                    "subtitle": hero_subtitle,
                    "badge": "CLINICAL BOTANICAL SCIENCE",
                    "ctaText": "Shop Verified Formulas"
                }
            })
            action_descriptions.append(f"Updated hero headline to: '{hero_title}'.")

        # 4. PRODUCT FILTERING AUTOMATION
        price_num = None
        if any(w in q_lower for w in ["under", "below", "less than", "cheaper than", "max price", "budget"]):
            price_num = parse_spoken_number(query)

        filter_concern = None
        if any(w in q_lower for w in ["hair fall", "thinning", "hair loss", "density"]):
            filter_concern = "Hair Fall & Thinning"
        elif any(w in q_lower for w in ["damage", "damaged", "dry", "broken", "bleached", "bond"]):
            filter_concern = "Damaged & Dry Hair"
        elif any(w in q_lower for w in ["dandruff", "scalp buildup", "oily", "flaky", "itchy", "clarifying"]):
            filter_concern = "Dandruff & Oily Scalp"
        elif any(w in q_lower for w in ["frizz", "heat", "thermal", "straighten", "blow dry"]):
            filter_concern = "Frizz & Heat Protection"
        elif any(w in q_lower for w in ["curly", "coils", "waves", "3a", "4c", "curl"]):
            filter_concern = "Curly, Coily & Wavy (3A-4C)"
        elif any(w in q_lower for w in ["color", "blonde", "brassiness", "purple shampoo", "dye"]):
            filter_concern = "Color Care & Blonde Tone"

        if price_num is not None or filter_concern:
            payload = {}
            if price_num is not None:
                payload["maxPrice"] = float(price_num)
            if filter_concern:
                payload["hairConcern"] = filter_concern

            commands.append({
                "action": "FILTER_PRODUCTS",
                "payload": payload
            })
            desc = "Filtered catalog"
            if filter_concern: desc += f" for '{filter_concern}'"
            if price_num is not None: desc += f" under ${price_num:.2f}"
            action_descriptions.append(desc + ".")

        # 5. CART AUTOMATION & CONTEXTUAL ADD-MORE
        cart_triggers = ["add to cart", "buy", "purchase", "order", "put in cart", "add two", "add 2", "add 3", "add to my bag", "to cart", "in my cart", "to my cart", "add one more", "add another", "add 1 more", "one more"]
        if any(w in q_lower for w in cart_triggers) or (("cart" in q_lower or "bag" in q_lower) and any(w in q_lower for w in ["add", "put", "order", "get"])) or ("add" in q_lower and any(w in q_lower for w in ["more", "another", "extra", "bottle"])):
            all_prods = self.db.get_all_products()
            matched_prod = None

            for p in all_prods:
                p_name_words = set(re.findall(r'[a-z]+', p['name'].lower()))
                q_words = set(re.findall(r'[a-z]+', q_lower))
                overlap = p_name_words.intersection(q_words)

                # Prioritize direct ingredient/name match
                if any(w in q_lower for w in ["rosemary", "biotin"]) and "rosemary" in p["id"]:
                    matched_prod = p
                    break
                elif any(w in q_lower for w in ["peptide", "bond", "mask"]) and "peptide" in p["id"]:
                    matched_prod = p
                    break
                elif any(w in q_lower for w in ["scrub", "salicylic", "aha", "bha", "dandruff"]) and "scrub" in p["id"]:
                    matched_prod = p
                    break
                elif any(w in q_lower for w in ["heat", "thermo", "mist", "shield"]) and "heat" in p["id"]:
                    matched_prod = p
                    break
                elif any(w in q_lower for w in ["curl", "hibiscus", "butter", "coily"]) and "curl" in p["id"]:
                    matched_prod = p
                    break
                elif any(w in q_lower for w in ["amla", "oil", "elixir"]) and "oil" in p["id"]:
                    matched_prod = p
                    break
                elif len(overlap) >= 2:
                    matched_prod = p
                    break

            # If no product found in query but context has a product
            if not matched_prod and context:
                for p in all_prods:
                    if p["name"].lower() in context.lower():
                        matched_prod = p
                        break

            if not matched_prod and all_prods:
                matched_prod = all_prods[0]

            if matched_prod:
                qty = extract_cart_quantity(query) if ("one more" not in q_lower and "another" not in q_lower) else 1
                commands.append({
                    "action": "ADD_TO_CART",
                    "payload": {
                        "productId": matched_prod["id"],
                        "productName": matched_prod["name"],
                        "price": matched_prod["price"],
                        "quantity": qty
                    }
                })
                action_descriptions.append(f"Added {qty} item(s) of '{matched_prod['name']}' to cart.")

        # 6. PRODUCT PRICE UPDATE AUTOMATION
        if ("price" in q_lower or "$" in query) and any(w in q_lower for w in ["change", "update", "set", "through", "to $", "is $", "reduce", "increase", "make it"]):
            from agents.product_agent import ProductManagementAgent
            prod_agent = ProductManagementAgent()
            price_res = prod_agent.update_price_from_query(query)
            if price_res.get("ui_command"):
                commands.append(price_res["ui_command"])
                action_descriptions.append(price_res["details"])

        # 7. CARD SIZING & VISUAL COMPONENT STYLING
        if any(w in q_lower for w in ["card size", "card width", "smaller card", "larger card", "shrink card", "reduce card", "card dimensions", "compact card", "grid size"]):
            target_prod = "rosemary" if "rosemary" in q_lower else ("all" if "all" in q_lower else "rosemary")
            is_smaller = any(w in q_lower for w in ["reduce", "smaller", "shrink", "compact", "decrease", "tight"])
            new_width = "220px" if is_smaller else "340px"
            new_padding = "14px" if is_smaller else "28px"
            new_scale = 0.88 if is_smaller else 1.05

            commands.append({
                "action": "UPDATE_CARD_STYLE",
                "payload": {
                    "target": target_prod,
                    "isSmaller": is_smaller,
                    "maxWidth": new_width,
                    "padding": new_padding,
                    "scale": new_scale,
                    "description": f"Adjusted card size for '{target_prod}' to {new_width} (scale: {new_scale})."
                }
            })
            action_descriptions.append(f"Updated product card dimensions for '{target_prod}' ({'Compact' if is_smaller else 'Expanded'}).")

        # 8. ROUTINE BUILDER MODAL LAUNCH
        if any(w in q_lower for w in ["diagnose", "routine quiz", "regimen builder", "find my routine", "consultation quiz"]):
            commands.append({
                "action": "LAUNCH_ROUTINE_BUILDER",
                "payload": {"hairConcern": filter_concern or "Hair Fall & Thinning"}
            })
            action_descriptions.append("Launched interactive trichology routine diagnostic quiz.")

        # 9. UI DEVELOPER MODE ACTIONS (Dynamic CSS, JSX Injection, Custom CSS)
        if any(w in q_lower for w in ["inject css", "custom style", "custom css", "change background to", "set background"]):
            css_match = re.search(r'css[:\s]+["\']?([^"\']+)["\']?', query, re.IGNORECASE)
            css_content = css_match.group(1) if css_match else None

            if not css_content and "background" in q_lower:
                css_content = f":root, html, body {{ --bg-primary: #{'1f0408' if 'red' in q_lower else '071526'}; }}"

            if css_content:
                commands.append({
                    "action": "SET_CUSTOM_CSS",
                    "payload": {"css": css_content}
                })
                action_descriptions.append("Applied dynamic CSS injection rules.")

        duration_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "agent": self.agent_name,
            "status": "success",
            "commands": commands,
            "actions_taken": action_descriptions,
            "has_mutations": len(commands) > 0,
            "execution_time_ms": duration_ms
        }

