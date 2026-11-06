# Dataset Forge

**Dataset Forge** (`pip install python-dataset-forge`) is a generator for
synthetic conversational and tool-calling data, built for training and
evaluating AI models. The generation templates cover human-robot
interaction (HRI) in a medical context (a hospital service robot talking
to patients and visitors) and a German smart-home assistant controlling
lights, heating and a vacuum robot, and the template system can easily be
expanded to other domains.

This project was started during the work on a scientific paper (Bachelor's
thesis) at the University of Augsburg, Germany, and will be expanded over
time.

## Quick Start

```bash
pip install -e .                       # from a clone of this repository

dforge init my-project --domain shop   # project folder with a first domain pack
cd my-project
dforge domains                         # yours plus the built-in hospital and home_assistant
dforge generate --domain shop --seed 1 # writes Synthetic_Data/ and Datasets/
```

Or from Python:

```python
from dataset_forge import Forge

forge = Forge("hospital", seed=42)
datapoints = list(forge.generate("tool_use/patient_reminder", n=5))
```

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
Chair of Human Computer Interaction, Prof. Dr. Elisabeth André 

The University of Augsburg has not claimed ownership of this project so
far, but it retains the right to do so. Material already released under an
open license stays available under that license.

## License

- **Code (this repository):** [MIT License](./LICENSE),
  Copyright © 2026 Benedict Wohlgemuth, University of Augsburg.
- **Datasets (Hugging Face):** [Creative Commons Attribution 4.0
  International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/),
  Copyright © 2026 Benedict Wohlgemuth, Dr. Matthias Kraus, Prof. Dr. Elisabeth André, University of Augsburg.

When you use the code or the datasets, please give appropriate credit to
the author and the University of Augsburg, and keep the copyright notice.

## Citation

If you use this generator or the datasets, please cite:

```bibtex
@software{wohlgemuth2026syntheticconversational,
  author       = {Wohlgemuth, Benedict, Dr. Matthias Kraus, Prof. Dr. Elisabeth André},
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