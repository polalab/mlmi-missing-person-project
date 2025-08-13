import torch
torch.cuda.empty_cache()

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
print(torch.version.cuda)
print(torch.__version__)
print("CUDA Available:", torch.cuda.is_available())
if  torch.cuda.get_device_name(0):
    print("GPU Name:", torch.cuda.get_device_name(0))
else:
    print("No GPU")
    raise ValueError("No GPU available")



# # Fix 1: Use device parameter instead of device_map for pipeline
# # Fix 2: Add trust_remote_code=True for better compatibility
# pipe = pipeline(
#     "text-generation",
#     model=model_id,
#     model_kwargs={"torch_dtype": torch.bfloat16},
#     device=device_index,  # Use device parameter
#     trust_remote_code=True
# )



# # messages = [
#     {"role": "system", "content": "You are a pirate chatbot who always responds in pirate speak!"},
#     {"role": "user", "content": "Who are you?"},
# ]



# # Fix 3: Use the same pipeline instance
# result = pipe("Hey how are you doing today?", max_new_tokens=100)
# print(result[0]["generated_text"])

def ask_open_llama(prompt, model="meta-llama/Meta-Llama-3.1-8B-Instruct", maxtokens=None, system_prompt="You are a police search advisor whose task is to summarise data.", temperature=0.1):
    print(torch.__version__)
    print("CUDA Available:", torch.cuda.is_available())
    print("GPU Name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    device_index = 0 if device == "cuda" else -1 
        
    model_id = model

        
    pipe = pipeline(
        "text-generation",
        model=model_id,
        model_kwargs={"torch_dtype": torch.bfloat16},
        device=device_index,  # Use device parameter
        trust_remote_code=True
    )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    outputs = pipe(
        messages,
        max_new_tokens=maxtokens,
        temperature=0.1,
    )
    print(outputs[0]["generated_text"][-1])

    return outputs[0]["generated_text"][-1]['content']