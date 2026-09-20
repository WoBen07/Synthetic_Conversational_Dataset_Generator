# Synthetic Conversational Dataset Generator

A generator for synthetic conversational data, built for training and
evaluating AI models. So far the generation templates cover human-robot
interaction (HRI) in a medical context (a hospital service robot talking
to patients and visitors), but the template system can easily be expanded
to other domains.

This project was started during the work on a scientific paper (Bachelor's
thesis) at the University of Augsburg, Germany, and will be expanded over
time.

## Documentation

For setup, usage, and the template system, see the technical
documentation in [`./documentation`](./documentation).

## Datasets

The datasets generated with this project are published on Hugging Face:

**[huggingface.co/datasets/Verox132/Medical_Conversational_Dataset](https://huggingface.co/datasets/Verox132/Medical_Conversational_Dataset)**

The dataset card there describes the categories, file formats, and known
limitations. New categories and dataset versions will be added over time.

```python
from datasets import load_dataset

ds = load_dataset("Verox132/Medical_Conversational_Dataset", "default")
```

All generated data is fully synthetic. Every name, patient ID, room
number, and appointment is randomly generated, and nothing in the datasets
was collected from real patients, hospitals, or interactions.

## Project Status

The project is under active development. More templates, categories, and
dataset versions will follow, and an evaluation of models on the released
dataset is planned.

## Authorship and Affiliation

Developed by **Benedict Wohlgemuth** under the guidance of
**Dr. Matthias Kraus**, as part of a Bachelor's thesis at:

Universität Augsburg
Universitätsstraße 2
86159 Augsburg, Germany

The University of Augsburg has not claimed ownership of this project so
far, but it retains the right to do so. Material already released under an
open license stays available under that license.

## License

- **Code (this repository):** [MIT License](./LICENSE),
  Copyright © 2026 Benedict Wohlgemuth, University of Augsburg.
- **Datasets (Hugging Face):** [Creative Commons Attribution 4.0
  International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/),
  Copyright © 2026 Benedict Wohlgemuth, University of Augsburg.

When you use the code or the datasets, please give appropriate credit to
the author and the University of Augsburg, and keep the copyright notice.

## Citation

If you use this generator or the datasets, please cite:

```bibtex
@software{wohlgemuth2026syntheticconversational,
  author       = {Wohlgemuth, Benedict},
  title        = {Synthetic Conversational Dataset Generator},
  year         = {2026},
  publisher    = {University of Augsburg},
  url          = {https://github.com/WoBen07/Synthetic_Conversational_Dataset_Generator}
}
```

## Disclaimer

The generated data is synthetic and not clinically validated. It is not a
source of medical advice, and models trained on it should not be deployed
to give medical advice. The software and datasets are provided "as is",
without warranty of any kind.

## Contributing and Contact

Questions, bug reports, and suggestions for new templates or domains are
welcome via
[GitHub Issues](https://github.com/WoBen07/Synthetic_Conversational_Dataset_Generator/issues).