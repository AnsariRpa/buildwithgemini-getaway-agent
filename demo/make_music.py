import numpy as np
import scipy.io.wavfile as wavfile

def generate_lofi_track(filename="/config/Desktop/BuildWithGemini/demo/lofi_music.wav", duration_sec=42, sample_rate=44100):
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    total_samples = len(t)
    
    # 84 BPM Upbeat Lo-Fi Hip Hop Groove
    bpm = 84
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4
    
    # 1. Warm Electric Piano chords (Fmaj7 -> Em7 -> Dm7 -> Cmaj7)
    chords = [
        [174.61, 220.0, 261.63, 329.63], # Fmaj7
        [164.81, 196.0, 246.94, 293.66], # Em7
        [146.83, 174.61, 220.0, 261.63], # Dm7
        [130.81, 164.81, 196.0, 246.94], # Cmaj7
    ]
    
    piano = np.zeros(total_samples, dtype=np.float32)
    bar_samples = int(bar_sec * sample_rate)
    num_bars = int(duration_sec / bar_sec) + 1
    
    # Lo-Fi wow & flutter
    flutter = 1.0 + 0.0025 * np.sin(2 * np.pi * 0.5 * t) + 0.0015 * np.sin(2 * np.pi * 2.1 * t)
    
    for b in range(num_bars):
        chord = chords[b % len(chords)]
        bar_start = int(b * bar_samples)
        
        for beat_idx in [0, 2.5]: # upbeat syncopated chord stabs
            chord_start = bar_start + int(beat_idx * beat_sec * sample_rate)
            if chord_start >= total_samples:
                break
            decay_len = int(2.0 * sample_rate)
            chord_end = min(total_samples, chord_start + decay_len)
            sub_t = np.linspace(0, (chord_end - chord_start)/sample_rate, chord_end - chord_start)
            env = np.exp(-sub_t * 2.0)
            
            for freq in chord:
                tone = np.sin(2 * np.pi * freq * flutter[chord_start:chord_end] * sub_t)
                tone += 0.35 * np.sin(4 * np.pi * freq * flutter[chord_start:chord_end] * sub_t)
                piano[chord_start:chord_end] += (tone * env * 0.09).astype(np.float32)

    # 2. Chill drums
    beat_samples = int(beat_sec * sample_rate)
    drums = np.zeros(total_samples, dtype=np.float32)
    num_beats = int(duration_sec / beat_sec)
    
    for i in range(num_beats):
        b_pos = int(i * beat_samples)
        beat_in_bar = i % 4
        
        # Kick on beat 1 and syncopated beat 3.5
        if beat_in_bar == 0 or (beat_in_bar == 2 and (i // 4) % 2 == 1):
            k_len = int(0.20 * sample_rate)
            if b_pos + k_len < total_samples:
                kt = np.linspace(0, 0.20, k_len)
                k_freq = 130.0 * np.exp(-kt * 24) + 48.0
                k_phase = np.cumsum(2 * np.pi * k_freq / sample_rate)
                kick = np.sin(k_phase) * np.exp(-kt * 14) * 0.4
                drums[b_pos:b_pos+k_len] += kick.astype(np.float32)
                
        # Snare rimshot on 2 and 4
        if beat_in_bar in [1, 3]:
            s_len = int(0.18 * sample_rate)
            if b_pos + s_len < total_samples:
                st = np.linspace(0, 0.18, s_len)
                noise = (np.random.rand(s_len) * 2 - 1) * np.exp(-st * 28)
                body = np.sin(2 * np.pi * 185 * st) * np.exp(-st * 20) * 0.3
                snare = (noise * 0.25 + body) * 0.32
                drums[b_pos:b_pos+s_len] += snare.astype(np.float32)
                
        # Swing hi-hats
        for sub in [0, 0.54]:
            h_pos = b_pos + int(sub * beat_samples)
            h_len = int(0.05 * sample_rate)
            if h_pos + h_len < total_samples:
                ht = np.linspace(0, 0.05, h_len)
                hh_noise = (np.random.rand(h_len) * 2 - 1) * np.exp(-ht * 80) * 0.075
                drums[h_pos:h_pos+h_len] += hh_noise.astype(np.float32)

    # 3. Walking Lo-Fi Bass
    bass = np.zeros(total_samples, dtype=np.float32)
    root_freqs = [87.31, 82.41, 73.42, 65.41]
    for b in range(num_bars):
        rf = root_freqs[b % len(root_freqs)]
        bar_start = int(b * bar_samples)
        for beat_idx in [0, 1.5, 2.5]:
            note_start = bar_start + int(beat_idx * beat_sec * sample_rate)
            if note_start >= total_samples:
                break
            n_len = int(1.1 * sample_rate)
            n_end = min(total_samples, note_start + n_len)
            bt = np.linspace(0, (n_end - note_start)/sample_rate, n_end - note_start)
            b_env = np.exp(-bt * 2.8)
            bass_tone = np.sin(2 * np.pi * rf * bt) * b_env * 0.28
            bass[note_start:n_end] += bass_tone.astype(np.float32)

    # 4. Vinyl Crackle
    crackle = (np.random.rand(total_samples) * 2 - 1) * 0.009
    click_indices = np.random.choice(total_samples, size=int(duration_sec * 6), replace=False)
    crackle[click_indices] += (np.random.rand(len(click_indices)) * 0.15 - 0.075)

    mix = piano + drums + bass + crackle
    
    # Smooth fades
    fade_in = np.minimum(1.0, np.linspace(0, 1.5, int(1.5 * sample_rate)))
    fade_out = np.minimum(1.0, np.linspace(3.0, 0, int(3.0 * sample_rate)))
    mix[:len(fade_in)] *= fade_in
    mix[-len(fade_out):] *= fade_out
    
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = (mix / peak) * 0.85
        
    mix_16bit = (mix * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, mix_16bit)
    print("Lo-fi music generated successfully at:", filename)

if __name__ == "__main__":
    generate_lofi_track()
