import ast


def calculate_node_similarity(node1, node2):
    """
    Berechnet die Ähnlichkeit zwischen zwei AST-Nodes (0.0 bis 1.0).
    Nutzt Bigram-Similarity auf dem unparsed Source Code.
    """
    # 1. Guard Clauses: Wenn einer None ist, ist Ähnlichkeit 0
    if node1 is None or node2 is None:
        return 0.0

    # 2. AST zu String wandeln (Normalisierter Code)
    # ast.unparse garantiert, dass 'x=1' und 'x = 1' gleich aussehen.
    try:
        str1 = ast.unparse(node1)
        str2 = ast.unparse(node2)
    except Exception:
        # Fallback für Nodes, die nicht unparsed werden können (selten)
        str1 = str(node1)
        str2 = str(node2)

    # 3. Wenn Strings identisch sind -> 100% (spart Rechenzeit)
    if str1 == str2:
        return 1.0

    # 4. Bigrams generieren
    def get_bigrams(text):
        # Wir entfernen Whitespaces für den Vergleich, um noch robuster zu sein
        text = text.replace(" ", "").replace("\n", "")
        return [text[i:i+2] for i in range(len(text) - 1)]

    bigrams1 = get_bigrams(str1)
    bigrams2 = get_bigrams(str2)

    # 5. Berechnung (Sørensen-Dice)
    len1 = len(bigrams1)
    len2 = len(bigrams2)

    if len1 == 0 and len2 == 0:
        return 1.0  # Beide leer -> gleich
    if len1 == 0 or len2 == 0:
        return 0.0

    # Schnittmenge berechnen (Nutze set für einfache Schnittmenge)
    # Für mathematisch exaktere Ergebnisse bei doppelten Bigrammen
    # könnte man collections.Counter nutzen, aber set reicht hier oft.
    intersection = len(set(bigrams1) & set(bigrams2))

    similarity = (2.0 * intersection) / (len1 + len2)
    return similarity

# --- BEISPIEL TEST ---


# Szenario: Tippfehler oder kleine Änderung
code_a = "def calculate(a, b): return a + b"
code_b = "def calculate(a, b): return a * b"  # Nur Operator geändert

node_a = ast.parse(code_a).body[0]
node_b = ast.parse(code_b).body[0]

score = calculate_node_similarity(node_a, node_b)
print(f"Similarity: {score:.4f}")
# Erwartet: Sehr hoch (> 0.8), da fast alles gleich ist.

# Szenario: Komplett anders
code_c = "class User: pass"
node_c = ast.parse(code_c).body[0]

score_diff = calculate_node_similarity(node_a, node_c)
print(f"Similarity diff: {score_diff:.4f}")
# Erwartet: Sehr niedrig (< 0.2)
