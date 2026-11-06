counter = 0


def patient_id():

    global counter

    counter += 1

    return f"p{counter:03}"


def appointment_id():

    global counter

    counter += 1

    return f"a{counter:03}"