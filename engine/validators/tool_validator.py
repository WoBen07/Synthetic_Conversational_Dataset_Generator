class ToolValidator:

    def validate(self, datapoint):

        errors = []

        messages = datapoint["messages"]

        for i in range(len(messages)-1):

            current = messages[i]

            nxt = messages[i+1]

            if (
                current["role"] == "assistant"
                and "tool_call" in current
            ):

                if nxt["role"] != "tool":

                    errors.append(
                        f"Tool call at {i} not followed by tool response"
                    )

                    continue


                if (
                    current["tool_call"]["name"]
                    != nxt["name"]
                ):

                    errors.append(

                        f"Tool mismatch at {i}"

                    )

        return errors