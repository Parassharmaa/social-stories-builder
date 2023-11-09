import os
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    ImageSequenceClip,
    concatenate_videoclips,
)
from io import BytesIO

from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips


def merge_images_audio_to_video(
    image_files,
    audio_files,
    output_file,
    fps=10,
    slide_transition_duration=1,
    break_duration=1,
):
    # Check if the number of images and audio files match
    if len(image_files) != len(audio_files):
        raise ValueError("Number of images and audio files must match")

    audio_clips = [AudioFileClip(audio_file) for audio_file in audio_files]

    video_clips = []
    for i in range(len(image_files)):
        image_clip = ImageClip(image_files[i], duration=audio_clips[i].duration)

        if i > 0:
            # Add a break (static frame) between clips
            break_duration_frames = int(break_duration * fps)
            break_clip = ImageClip(image_files[i], duration=break_duration_frames / fps)
            video_clips.append(break_clip)

        video_clip = image_clip.set_audio(audio_clips[i])
        video_clips.append(video_clip)

    final_video = concatenate_videoclips(video_clips, method="compose")

    final_video.write_videofile(output_file, codec="libx264", fps=fps)

    return output_file


if __name__ == "__main__":
    image_files = [
        f"images/lighting_diya/{i}" for i in os.listdir("images/lighting_diya")
    ]

    audio_files = [
        f"audio/lighting_diya/{i}" for i in os.listdir("audio/lighting_diya")
    ]

    output_file = f"{os.urandom(16).hex()}.mp4"

    print(audio_files)

    print(image_files)

    merge_images_audio_to_video(image_files, audio_files, output_file)
