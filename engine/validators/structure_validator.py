class StructureValidator:

    def validate(self, datapoint):

        errors = []

        if "messages" not in datapoint:

            errors.append("Missing messages")

            return errors


        messages = datapoint["messages"]

        if not messages:

            errors.append("Empty conversation")

            return errors


        # A conversation starts with the user, or with a system message
        # that sets the scene (e.g. the robot entering a room). Never
        # with the robot talking out of nowhere.
        if messages[0].get("role") not in ("system", "user"):

            errors.append(
                f"Conversation starts with '{messages[0].get('role')}', "
                f"expected 'system' or 'user'"
            )


        for i, message in enumerate(messages):

            if "role" not in message:

                errors.append(
                    f"Message {i} missing role"
                )


            role = message.get("role")


            if role == "system" and i != 0:

                errors.append(
                    f"System message at {i}, only allowed first"
                )


            if role == "assistant":

                content = message.get("content")

                has_text = isinstance(content, str) and content.strip()

                if (
                    not has_text
                    and "tool_call" not in message
                    and "tool_calls" not in message
                ):

                    errors.append(
                        f"Assistant message {i} has neither content nor tool_call"
                    )


            elif role == "tool":

                if "name" not in message:

                    errors.append(
                        f"Tool message {i} missing name"
                    )

                # The robot has to react to a tool result before the
                # user speaks again.
                if (
                    i + 1 < len(messages)
                    and messages[i + 1].get("role") != "assistant"
                ):

                    errors.append(
                        f"Tool message {i} not followed by an assistant turn"
                    )


            elif role in ("user", "system"):

                if not str(message.get("content") or "").strip():

                    errors.append(
                        f"{role.capitalize()} message {i} missing content"
                    )

        return errors