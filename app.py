# app.py  — minimal Gradio wrapper for Spaces
import os
import asyncio
import gradio as gr
from quiz_solver import QuizSolver

# Use environment variables (set these in the Space Secrets UI)
YOUR_EMAIL = os.getenv("EMAIL")
YOUR_SECRET = os.getenv("SECRET")

if not (YOUR_EMAIL and YOUR_SECRET):
    # When local debugging you can load a .env, but do NOT commit it to repo
    print("WARNING: EMAIL or SECRET not set as env vars. Set them in Space Secrets.")

async def run_solver_async(email, secret, url):
    solver = QuizSolver(email, secret)
    # run solve_quiz_chain and capture result summary
    try:
        await solver.solve_quiz_chain(url)
        return "Solver finished. Check logs for details."
    except Exception as e:
        return f"Solver error: {e}"

def run_solver(email, secret, url):
    # sync wrapper used by Gradio UI
    return asyncio.run(run_solver_async(email, secret, url))

with gr.Blocks() as demo:
    gr.Markdown("# LLM Quiz Solver (demo)")
    email_input = gr.Textbox(label="Email", value=os.getenv("EMAIL") or "")
    secret_input = gr.Textbox(label="Secret", value=os.getenv("SECRET") or "", type="password")
    url_input = gr.Textbox(label="Quiz URL", value="https://tds-llm-analysis.s-anand.net/project2")
    run_btn = gr.Button("Start solver (this runs background task)")
    output = gr.Textbox(label="Status")

    run_btn.click(
    fn=run_solver,
    inputs=[email_input, secret_input, url_input],
    outputs=[output],
    api_name="solve")

demo.queue()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
