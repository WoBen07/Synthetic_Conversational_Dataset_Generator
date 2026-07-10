import json
from datetime import datetime
from pathlib import Path



class MetadataWriter:


    def write(
        self,
        output_dir,
        metadata
    ):

        path = Path(output_dir)

        path.mkdir(
            parents=True,
            exist_ok=True
        )


        metadata_file = path / "metadata.json"


        with open(
            metadata_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                metadata,
                file,
                indent=2,
                ensure_ascii=False
            )