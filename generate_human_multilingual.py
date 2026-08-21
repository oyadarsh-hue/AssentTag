# -*- coding: utf-8 -*-
import os
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
from moviepy.audio.fx.all import volumex

video_path = "d:\\AssentTag\\assentag - Copy (2)\\static\\assets\\generated_final_video.mp4"
output_path = "d:\\AssentTag\\assentag - Copy (2)\\static\\assets\\assenttag_multilingual_human.mp4"

print("1. Generating English Audio...")
en_text = "Welcome to AssentTag, the ultimate social media and facial privacy network. During registration, we use a strict zero point four two mathematical AI threshold to completely prevent identical siblings from triggering false duplicate account blocks. When photos are uploaded, zero storage dynamic EXIF blurring mathematically scrambles unauthorized faces in real time before they ever reach the browser."
gTTS(text=en_text, lang='en', tld='com').save("temp_en.mp3")

print("2. Generating Hindi Audio...")
hi_text = "सिस्टम में आपका स्वागत है। रजिस्ट्रेशन के दौरान, हम डुप्लिकेट अकाउंट को रोकने के लिए एआई थ्रेशोल्ड का उपयोग करते हैं। हमारी शक्तिशाली प्रणाली बिना स्टोरेज के सीधे सर्वर रैम में फोटो को धुंधला कर देती है।"
gTTS(text=hi_text, lang='hi').save("temp_hi.mp3")

print("3. Generating Malayalam Audio...")
ml_text = "നിങ്ങളുടെ മുഖം സുരക്ഷിതമാക്കാൻ ഞങ്ങൾ ഇവിടെയുണ്ട്. ഇരട്ട അക്കൗണ്ടുകൾ തടയാൻ കർശനമായ സുരക്ഷാ സംവിധാനങ്ങൾ ഉണ്ട്. ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുമ്പോൾ മറ്റുള്ളവരുടെ മുഖം സ്വയമേവ മറയ്ക്കപ്പെടുന്നു. ലൈവ് വെബ്ക്യാം സ്കാനിംഗ് വഴി നിങ്ങളുടെ അക്കൗണ്ട് ഹാക്കർമാരിൽ നിന്നും പൂർണ്ണമായും സുരക്ഷിതമാക്കുന്നു."
gTTS(text=ml_text, lang='ml').save("temp_ml.mp3")

print("4. Processing Video & Merging Audio...")
video = VideoFileClip(video_path)

# Mute the original video to ensure a clean voiceover
video = video.without_audio()

# Loop the video to reach 120 seconds
num_loops = int(120 / video.duration) + 1
looped_video = concatenate_videoclips([video] * num_loops).subclip(0, 120)

# Load Audio Clips
audio_en = AudioFileClip("temp_en.mp3").set_start(1)
audio_hi = AudioFileClip("temp_hi.mp3").set_start(45)
audio_ml = AudioFileClip("temp_ml.mp3").set_start(80)

final_audio = CompositeAudioClip([audio_en, audio_hi, audio_ml])
final_video = looped_video.set_audio(final_audio)

print("5. Exporting Multilingual H.264 Video...")
final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)

# Cleanup
for f in ["temp_en.mp3", "temp_hi.mp3", "temp_ml.mp3"]:
    if os.path.exists(f): os.remove(f)

print("Generation Complete!")
