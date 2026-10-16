from api_details import a_key
import google.generativeai as genai
class correcting:
    def correct_transcription(word_timings):

        segments = []
        current_segment = []
        current_timing = {'start': None, 'end': None}
            
        for i, word_info in enumerate(word_timings):
            if current_segment == []:
                current_timing['start'] = word_info['start_time']
                current_segment.append(word_info['word'])
            else:
                    # Check if there's a significant pause
                time_gap = word_info['start_time'] - word_timings[i-1]['end_time']
                if time_gap > 0.35:  
                    current_timing['end'] = word_timings[i-1]['end_time']
                    segments.append({
                        'text': ' '.join(current_segment),
                        'timing': current_timing.copy()
                    })
                    current_segment = [word_info['word']]
                    current_timing['start'] = word_info['start_time']
                else:
                    current_segment.append(word_info['word'])
        if current_segment:
            current_timing['end'] = word_timings[-1]['end_time']
            segments.append({
                'text': ' '.join(current_segment),
                'timing': current_timing.copy()
            })
        print(segments)
        try:
            api_pass = a_key.pass_key()
            genai.configure(api_key=api_pass)
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            enhanced_segments = []
            print(2)
            for segment in segments:
                
                text = f"""
                text: "{segment['text']}"
                Correct grammar and remove filler words while keeping the same general length and meaning. Preserve key timing and pacing. give the corrected text as output and if there is silence return em404$
                """

                response = model.generate_content(text, stream=False)
                response.resolve()
                t = response.text
                t = t.replace("\n",'')
                if "em404$" in t:
                    t = None
                enhanced_segments.append({
                    'text': t,
                    'timing': segment['timing']
                })
            return [True,enhanced_segments]
        except Exception as e:
                return [False,e]


