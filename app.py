import gradio as gr
from openai import OpenAI
import os
import requests
from merge_audio_images import merge_images_audio_to_video

client = OpenAI()

social_story_prompt = """Generate social story for a child with special needs for the following theme, output each scene as a bullet point, no markdown and no headings, only points, max slides 5-6:

Theme: {theme}
Language: {language}

- 

"""

image_description_prompt = """Generate prompts for DALL-E for each scenes given below, output each description as a bullet point, no markdown and no headings, only points:

{script}

- 

"""


def run_completion(input, prompt, temperature=0.7):
    print("Prompt: ", prompt)
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=temperature,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": input},
        ],
    )

    print(completion)
    # tokens used
    output_token = completion.usage.completion_tokens
    input_token = completion.usage.prompt_tokens
    output_cost = output_token * 0.002 / 1000
    input_cost = input_token * 0.0015 / 1000
    return completion.choices[0].message.content, round(input_cost + output_cost, 5)


def generate_script(
    script_theme,
    language,
    temperature=0.7,
):
    script, cost = run_completion(
        input="",
        prompt=social_story_prompt.format(theme=script_theme, language=language),
        temperature=temperature,
    )
    print("Cost of Script: ", cost)
    return script


style = "Illustration, Cartoon, Image, realistic, sketch, colorful, young kids"


def generate_image_description(
    script,
    temperature=0.7,
):
    script, cost = run_completion(
        input="",
        prompt=image_description_prompt.format(script=script),
        temperature=temperature,
    )
    print("Cost of Script: ", cost)
    return script


def generate_images(
    image_description,
    temperature=0.7,
):
    # split the image description into list and remove - from each line
    image_description = image_description.split("\n")
    image_description = [i.replace("-", "").strip() for i in image_description]

    images = []
    for img in image_description:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"{img}, {style}",
            size="1024x1024",
            quality="standard",
            n=1,
        )
        print(img)
        images.append(response.data[0].url)

    local_images = []
    # save images to file
    for i, image in enumerate(images):
        response = requests.get(image)
        if response.status_code == 200:
            image_filename = f"images/image_{i}.jpg"
            local_images.append(image_filename)
            with open(image_filename, "wb") as f:
                f.write(response.content)
    return images, "\n".join(local_images)


def generate_audio(
    script,
    temperature=0.7,
):
    # split the image description into list and remove - from each line
    script = script.split("\n")
    script = [i.replace("-", "").strip() for i in script]

    script = [i for i in script if i != ""]

    audio_files = []
    for s in script:
        random_name = f"audio/{os.urandom(16).hex()}.mp3"
        response = client.audio.speech.create(model="tts-1", voice="nova", input=s)

        response.stream_to_file(random_name)
        audio_files.append(random_name)

    # create audio tag html for each audio file
    audio_html = ""
    for audio in audio_files:
        audio_html += f'<audio controls src="file/{audio}"></audio>'
    return audio_html, "\n".join(audio_files)


def render_video(
    image_files,
    audio_files,
):
    print(audio_files)

    print(image_files)

    audio_files = audio_files.split("\n")

    image_files = image_files.split("\n")

    outfile = merge_images_audio_to_video(
        image_files, audio_files, os.urandom(16).hex() + ".mp4"
    )
    return outfile


with gr.Blocks() as demo:
    with gr.Row():
        story_theme = gr.Textbox(
            label="Theme or Description about Social Story", lines=1, max_lines=2
        )
        story_language = gr.Dropdown(
            label="Language",
            choices=["English", "Hindi"],
            default="English",
        )

    script_btn = gr.Button("Generate")

    gr.Markdown("### Results")

    with gr.Row():
        script_output = gr.Textbox(label="Script", show_copy_button=True)
    image_desc_btn = gr.Button("Generate Image Descriptions")
    with gr.Row():
        image_description = gr.Textbox(label="Image Description", show_copy_button=True)

    generate_img_btn = gr.Button("Generate Images")

    image_gallery = gr.Gallery(columns=4)

    generate_audio_btn = gr.Button("Generate Audio")

    audio_files = gr.HTML("")

    render_video_btn = gr.Button("Render Video")

    video_gr = gr.Video()

    examples = gr.Examples(
        examples=[["Deepwali is a festival of lights."]],
        inputs=[story_theme],
    )

    inputs = [story_theme, story_language]
    script_btn.click(fn=generate_script, inputs=inputs, outputs=[script_output])

    image_desc_btn.click(
        fn=generate_image_description, inputs=script_output, outputs=[image_description]
    )

    local_images = gr.Textbox(label="Audio Files", visible=False)
    generate_img_btn.click(
        fn=generate_images,
        inputs=image_description,
        outputs=[image_gallery, local_images],
    )

    audio_files_src = gr.Textbox(label="Audio Files", visible=False)

    generate_audio_btn.click(
        fn=generate_audio, inputs=script_output, outputs=[audio_files, audio_files_src]
    )

    render_video_btn.click(
        fn=render_video, inputs=[local_images, audio_files_src], outputs=[video_gr]
    )

    demo.launch()
