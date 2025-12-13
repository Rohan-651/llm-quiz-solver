import os
import asyncio
import gradio as gr
from quiz_solver import QuizSolver


async def run_solver_async(email, secret, url):
    solver = QuizSolver(email, secret)
    try:
        await solver.solve_quiz_chain(url)
        return "Solver finished. Check logs for details."
    except Exception as e:
        return f"Solver error: {e}"


def run_solver(email, secret, url):
    return asyncio.run(run_solver_async(email, secret, url))


with gr.Blocks() as demo:
    gr.Markdown("# LLM Quiz Solver (demo)")

    email_input = gr.Textbox(
        label="Email",
        value=os.getenv("EMAIL", "")
    )

    secret_input = gr.Textbox(
        label="Secret",
        type="password",
        value=os.getenv("SECRET", "")
    )

    url_input = gr.Textbox(
        label="Quiz URL",
        value="https://tds-llm-analysis.s-anand.net/project2"
    )

    run_btn = gr.Button("Start solver (this runs background task)")
    output = gr.Textbox(label="Status")

    run_btn.click(
        fn=run_solver,
        inputs=[email_input, secret_input, url_input],
        outputs=[output]
    )

api = gr.Interface(
    fn=run_solver,
    inputs=[
        gr.Textbox(label="Email"),
        gr.Textbox(label="Secret", type="password"),
        gr.Textbox(label="Quiz URL")
    ],
    outputs=gr.Textbox(label="Status"),
    api_name="solve",
    visible=False
)

demo.queue()
api.queue()

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
