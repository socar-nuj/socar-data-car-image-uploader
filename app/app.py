import os
import shutil
import reflex as rx
import datetime
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

MAX_UPLOAD = os.getenv("MAX_UPLOAD", 30)

BUCKET_NAME = "false-detection-car-image"
DATE = datetime.datetime.now().date().isoformat()

color = "rgb(107,99,246)"


# class CheckboxState(rx.State):
#     checked_image_list: list[str]
#     checked_count: int = 0
#
#     def set_checked(self, image_name: str, checked: bool):
#         print(f"checked : {checked}")
#         print(f"image_name : {image_name}")
#         if checked and image_name not in self.checked_image_list:
#             self.checked_count += 1
#             self.checked_image_list.append(image_name)
#         elif not checked and image_name in self.checked_image_list:
#             self.checked_count -= 1
#             self.checked_image_list.remove(image_name)
#
#     def clear_checked(self):
#         self.checked_image_list = []
#         self.checked_count = 0


def upload_directory_to_gcs(source_directory_path: str):
    client = storage.Client()
    bucket = client.get_bucket(BUCKET_NAME)

    for root, _, files in os.walk(source_directory_path):
        for file in files:
            file_path = os.path.join(source_directory_path, file)
            blob_name = f"{DATE}/{file}"
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(file_path)

            print(f"Uploaded {file} to gs://{BUCKET_NAME}/{blob_name}")


class CarImageUpload(rx.State):
    img: list[str]
    uploading: bool = False
    total_file_number: int = 0
    outfile: str

    async def handle_upload(
        self, files: list[rx.UploadFile]
    ):
        for file in files:
            self.total_file_number += 1

            upload_data = await file.read()
            self.outfile = rx.get_upload_dir() / file.filename
            # Save the file.
            with self.outfile.open("wb") as file_object:
                file_object.write(upload_data)

            # Update the img var.
            self.img.append(file.filename)

    def upload_files(self):
        upload_directory_to_gcs(rx.get_upload_dir())

    def clear_all(self):
        self.img = []
        self.total_file_number = 0
        shutil.rmtree(rx.get_upload_dir())


def index():
    """The main view."""
    return rx.vstack(
        rx.upload(
            rx.vstack(
                rx.button(
                    "Select File",
                    color=color,
                    bg="white",
                    border=f"1px solid {color}",
                ),
                rx.text(
                    "Drag and drop files here or click to select files"
                ),
            ),
            id="upload_1",
            multiple=True,
            accept={
                "image/png": [".png"],
                "image/jpeg": [".jpg", ".jpeg"],
                "image/gif": [".gif"],
                "image/webp": [".webp"],
            },
            max_files=30,
            disabled=False,
            on_drop=CarImageUpload.handle_upload(
                rx.upload_files(upload_id="upload_1")
            ),
            border=f"1px dotted {color}",
            padding="5em",
        ),
        rx.grid(
            rx.foreach(
                CarImageUpload.img,
                lambda img: rx.vstack(
                    rx.image(src=rx.get_upload_url(img), width="150px", height="150px"),
                    rx.text(f"{img}"),
                    # rx.checkbox(
                    #     on_change=lambda checked: CheckboxState.set_checked(img, checked)
                    # ),
                    spacing="0.5em",
                    padding_left="1em",
                ),
            ),
            columns="5",
            spacing="10",
        ),
        rx.progress(value=CarImageUpload.total_file_number, max=MAX_UPLOAD),
        rx.stack(
            rx.button(
                "Upload",
                on_click=CarImageUpload.upload_files,
            ),
            rx.button(
                "Clear All",
                on_click=CarImageUpload.clear_all,
            ),
        ),
        rx.text(
            "total_file_number: ",
            CarImageUpload.total_file_number,
            f" / {MAX_UPLOAD}",
        ),
        # rx.text(
        #     "total_checked_number: ",
        #     CheckboxState.checked_count,
        # ),
        # rx.text(
        #     "checked_image_name: ",
        #     CheckboxState.checked_image_list,
        # ),
        align="center",
        padding="5em",
    )


app = rx.App()

app.add_page(index)
