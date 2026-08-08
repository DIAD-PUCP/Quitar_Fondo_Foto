import os

import rembg
from PIL import Image
from tqdm import tqdm


def resize_image(img, target_width, target_height):
    width, height = img.size  # Obtiene las dimensiones de la imagen
    original_aspect_ratio = (
        width / height
    )  # Guarda la relacion de las dimensiones de la imagen
    target_aspect_ratio = (
        target_width / target_height
    )  # Obtiene las dimensiones de la imagen a la que se desea convertir

    if original_aspect_ratio > target_aspect_ratio:
        # La imagen es más ancha que alta
        new_width = int(target_height * original_aspect_ratio)
        resized_img = img.resize((new_width, target_height), Image.BICUBIC)
        x_offset = (new_width - target_width) // 2
        resized_img = resized_img.crop(
            (x_offset, 0, x_offset + target_width, target_height)
        )
    else:
        # La imagen es más alta que ancha
        new_height = int(target_width / original_aspect_ratio)
        resized_img = img.resize((target_width, new_height), Image.BICUBIC)
        y_offset = (new_height - target_height) // 2
        resized_img = resized_img.crop(
            (0, y_offset, target_width, y_offset + target_height)
        )

    return resized_img, target_width, target_height


def main():
    providers = [
        (
            "TensorrtExecutionProvider",
            {
                "trt_fp16_enable": True,  # <-- ENABLES FP16
                "trt_max_workspace_size": 1 << 30,  # 1 GB workspace
                "trt_engine_cache_enable": True,  # Cache the built engine
                "trt_engine_cache_path": "./trt_cache",  # Cache folder
            },
        ),
        ("CUDAExecutionProvider", {}),  # Fallback if TensorRT fails
    ]
    s = rembg.new_session(
        model_name="birefnet-portrait",
        providers=providers,
    )
    input_dir = "inputs"
    outpur_dir = "outputs"
    files = (f"{input_dir}/{file}" for file in os.listdir(input_dir))
    for file in tqdm(files):
        img = Image.open(file)
        # img2, _, _ = resize_image(img, 240, 288)
        img2 = rembg.remove(img, session=s, bgcolor=(255, 255, 255, 255))
        img2.convert("RGB").save(
            f"{outpur_dir}/{file[len(input_dir) + 1 : -4]}.jpg",
            format="jpeg",
            dpi=(300, 300),
        )


if __name__ == "__main__":
    main()
