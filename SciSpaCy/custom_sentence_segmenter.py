import consts # pylint: disable-msg=E0611,E0401

def combined_rule_sentence_segmenter(doc):
    """Adds sentence boundaries to a Doc. Intended to be used as a pipe in a spaCy pipeline.

    @param doc: the spaCy document to be annotated with sentence boundaries
    """

    # keep track of the two previous tokens
    prev_tokens = [None, None]

    # keep stacks for determining when we are inside parenthesis or brackets
    parens_stack = []
    brackets_stack = []
    open_paren_to_stack = {"(": parens_stack, "[": brackets_stack}
    close_paren_to_stack = {")": parens_stack, "]": brackets_stack}
    for token in doc:
        # handling special quote symbols
        # for example: 'in word order or syntactic structure (e.g., “cats climb trees” vs. “trees climb cats”).'
        if token.text == '“' or token.text == '”':
            if prev_tokens[-1] and prev_tokens[-1].text != ".":
                doc[token.i].is_sent_start = False

        if token.text[0].isdigit():
            # handling an abbrevation followed by a number
            # for example: 'LSTM networks, which we review in Sec. 2, have been successfully'
            if prev_tokens[-1] and prev_tokens[-1].text in consts.ABBREVIATIONS:
                doc[token.i].is_sent_start = False

            # handle a bracket followed by a number
            # for example: 'environments such as Microsoft Robotics Studio [9] and Webots [10] have many'
            if prev_tokens[-1] and prev_tokens[-1].text == '[':
                doc[token.i].is_sent_start = False


        # sentences can only start with ( if there is a complete sentence within the parens
        # here a . is serving as a proxy for being a complete sentence
        # This isn't quite correct, as a sentence may start with (Bottom left) or [Bottom left]
        # and this prevents that from being segmented correctly
        open_parens = ["(", "["]
        close_parens = [")", "]"]
        if token.text in open_parens:
            open_paren_to_stack[token.text].append(token)
        if token.text in close_parens and close_paren_to_stack[token.text] != []:
            last_open_paren = close_paren_to_stack[token.text].pop()
            if prev_tokens[-1] and prev_tokens[-1].text != ".":
                # allow things like (A) or [A] to start a sentence
                if not (last_open_paren.i == (token.i-2) and len(prev_tokens[-1].text) == 1):
                    doc[last_open_paren.i].is_sent_start = False


        # if token.text == "(":
        #     open_parens.append(token)
        # if token.text == ")" and open_parens != []:
        #     last_open_paren = open_parens.pop()
        #     if prev_tokens[-1] and prev_tokens[-1].text != ".":
        #         # allow things like (A) to start a sentence
        #         if not (last_open_paren.i == (token.i-2) and len(prev_tokens[-1].text) == 1):
        #             doc[last_open_paren.i].is_sent_start = False

        # # same logic as above but for brackets instead of parens
        # if token.text == "[":
        #     open_brackets.append(token)
        # if token.text == "]" and open_brackets != []:
        #     last_open_bracket = open_brackets.pop()
        #     if prev_tokens[-1] and prev_tokens[-1].text != ".":
        #         # allow things like [A] to start a sentence
        #         if not (last_open_bracket.i == (token.i-2) and len(prev_tokens[-1].text) == 1):
        #             doc[last_open_bracket.i].is_sent_start = False

        # handling the case of a capital letter after a ) unless that was preceeded by a .
        # for example: 'the support of the Defense Advanced Resarch Projects Agency (DARPA) Deep Exploration'
        first_char = token.text[0]
        if first_char.isupper():
            if prev_tokens[-1] and prev_tokens[-1].text == ')':
                if prev_tokens[-2] and prev_tokens[-2].text != ".":
                    doc[token.i].is_sent_start = False

        # sentences cannot start with .
        if token.text == ".":
            doc[token.i].is_sent_start = False

        # attempt to handle double and quadruple new lines around
        # section headers by making them their own sentences
        # for example: '\n\n2 Long Short-Term Memory Networks\n\n\n\n2.1 Overview\n\n'
        if prev_tokens[-1] and (prev_tokens[-1].text == "\n\n\n\n" or prev_tokens[-1].text == "\n\n"):
            doc[token.i].is_sent_start = True
            doc[token.i-1].is_sent_start = True

        # update the saved previous tokens
        prev_tokens = prev_tokens[1:] + [token]

    # any unmatched parens should not be the start of a sentence
    for open_paren in parens_stack:
        doc[open_paren.i].is_sent_start = False

    # any unmatched brackets should not be the start of a sentence
    for open_bracket in brackets_stack:
        doc[open_bracket.i].is_sent_start = False

    return doc
