from flask import Flask, request, render_template, send_from_directory
import os
import ssl
from pytube import YouTube
import moviepy.editor as mp
from pydub import AudioSegment
from pysndfx import AudioEffectsChain

# Disable certificate verification (for educational purposes only)
ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    effect = request.form['effect']
    custom_name = request.form['custom_name']
    speed_ratio = float(request.form['speed_ratio'])
    pitch_shift = int(request.form['pitch_shift'])
    lowpass_cutoff = int(request.form['lowpass_cutoff'])
    bass_boost = request.form.get('bass_boost')
    gain_db = request.form.get('gain_db')
    oops = 'oops' in request.form
    phaser = 'phaser' in request.form
    tremolo = 'tremolo' in request.form
    compand = 'compand' in request.form
    no_reverb = 'no_reverb' in request.form

    if not validate_youtube_url(url):
        return "Invalid YouTube URL", 400
    output_dir = os.getcwd()
    video_filename = download_video(url, output_dir)
    if video_filename is None:
        return "Error downloading video", 500
    audio_input = convert_to_mp3(os.path.join(
        output_dir, video_filename), output_dir)
    if audio_input is None:
        return "Error converting video to MP3", 500
    audio_output = apply_effects(audio_input, effect, speed_ratio, pitch_shift, lowpass_cutoff,
                                 bass_boost, gain_db, oops, phaser, tremolo, compand, no_reverb, custom_name)
    return send_from_directory(output_dir, audio_output, as_attachment=True)


def validate_youtube_url(url):
    return url.startswith('https://www.youtube.com/watch') or url.startswith('https://youtu.be/')


def download_video(url, output_dir):
    try:
        youtube = YouTube(url)
        video = youtube.streams.get_highest_resolution()
        video_filename = video.default_filename.replace(" ", "_")
        video.download(filename=video_filename, output_path=output_dir)
        return video_filename
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None


def convert_to_mp3(video_path, output_dir):
    try:
        video = mp.VideoFileClip(video_path)
        audio = video.audio
        mp3_filename = os.path.splitext(
            os.path.basename(video_path))[0] + ".mp3"
        mp3_path = os.path.join(output_dir, mp3_filename)
        audio.write_audiofile(mp3_path, codec='libmp3lame')
        os.remove(video_path)
        return mp3_filename
    except Exception as e:
        print(f"Error converting to MP3: {e}")
        return None


def apply_effects(audio_input, effect, speed_ratio, pitch_shift, lowpass_cutoff, bass_boost, gain_db, oops, phaser, tremolo, compand, no_reverb, custom_name):
    if custom_name:
        output_name = custom_name + ".mp3"
    else:
        output_name = os.path.splitext(audio_input)[0] + f"_{effect}.mp3"

    try:
        fx = AudioEffectsChain()
        if bass_boost:
            fx = fx.custom(f'bass {bass_boost}')
        fx = fx.pitch(pitch_shift)
        if oops:
            fx = fx.custom("oops")
        if tremolo:
            fx = fx.tremolo(freq=500, depth=50)
        if phaser:
            fx = fx.phaser(0.9, 0.8, 2, 0.2, 0.5)
        if gain_db:
            fx = fx.gain(gain_db)
        if compand:
            fx = fx.compand()
        fx = fx.speed(speed_ratio).lowpass(lowpass_cutoff)
        if not no_reverb:
            fx = fx.reverb()

        fx(audio_input, output_name)
        return output_name
    except Exception as e:
        print(f"Error applying effects: {e}")
        return None


if __name__ == "__main__":
    app.run(debug=True)
