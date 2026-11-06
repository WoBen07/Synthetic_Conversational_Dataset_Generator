class ToolValidator:

    def validate(self, datapoint):

        errors = []

        messages = datapoint["messages"]

        for i in range(len(messages)-1):

            current = messages[i]

            nxt = messages[i+1]

            calls = self._tool_calls(current)

            if not calls:
                continue

            if nxt["role"] != "tool":

                errors.append(
                    f"Tool call at {i} not followed by tool response"
                )

                continue

            # A single assistant turn carries one tool call in this
            # dataset; if it ever carries more, they must still be answered
            # by a matching tool response as the next message.
            expected_names = {call.get("name") for call in calls}

            if nxt.get("name") not in expected_names:

                errors.append(
                    f"Tool mismatch at {i}"
                )

        return errors

    def _tool_calls(self, message):

        if message.get("role") != "assistant":
            return []

        plural = message.get("tool_calls")

        if plural:
            return list(plural) if isinstance(plural, list) else [plural]

        singular = message.get("tool_call")

        if singular:
            return [singular]

        return []
