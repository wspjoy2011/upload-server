from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class ImageDTO:
    """Data Transfer Object for image metadata.

    Attributes:
        filename (str): Name of the file in the storage system.
        original_name (str): Original name of the file when it was uploaded.
        size (int): Size of the file in bytes.
        file_type (str): File extension (.jpg, .png, or .gif).
    """
    filename: str
    original_name: str
    size: int
    file_type: str

    def as_dict(self) -> Dict[str, Any]:
        """Convert the DTO to a dictionary for serialization.

        Returns:
            Dict[str, Any]: Dictionary representation of the DTO.
        """
        return asdict(self)


@dataclass(kw_only=True)
class ImageDetailsDTO(ImageDTO):
    """Data Transfer Object for detailed image information.

    Attributes:
        id (int): Unique identifier of the image.
        filename (str): Name of the file in the storage system.
        original_name (str): Original name of the file when it was uploaded.
        size (int): Size of the file in bytes.
        file_type (str): File extension (.jpg, .png, or .gif).
        upload_time (str): ISO-formatted timestamp of when the image was uploaded.
    """
    id: int
    upload_time: str
