class StructureValidator:

    def validate(self, datapoint):

        errors = []

        if "messages" not in datapoint:

            errors.append("Missing messages")

            return errors


        for i, message in enumerate(datapoint["messages"]):

            if "role" not in message:

                errors.append(
                    f"Message {i} missing role"
                )


            role = message.get("role")


            if role == "assistant":

                if (
                    "content" not in message
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


            elif role == "user":

                if "content" not in message:

                    errors.append(
                        f"User message {i} missing content"
                    )

        return errors