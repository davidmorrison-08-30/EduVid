SUBAGENT_SYSTEM_PROMPT = """Your task is to resolve the overlapping and oversizing issues of displayed components in the generated code file that is 
later executed to generate an animation video. Read the generated Python code file which is to be executed to generate an animation video. 
Check if the coordinates and sizes of graphic components in the to-be-generated video are well aligned and fit with the scene. You must look for any overlaps between texts, components, equations, etc.
and look for any oversized texts, components, equations, etc. i.e. that are not fit within the video window size.
Then rewrite the file to fix these issues.

You are granted access to coding skills that will greatly aid you in modifying Python code for better video quality.
ONLY use ManimGL library and commands to accomplish the video.

## `manimgl-best-practices`
OpenGL-based animation engine with interactive development. Use this skill to modify Python code based on the scene specifications (`scenes.md` file)
"""

code_reviewer_subagent = {
    "name": "code-reviewer",
    # "description": (
    #     "Inspects generated code and improve text and component alignment"
    #     "Use this before executing the code"
    # ),
    "description": "Inspects generated code and improve text and component alignment. Use this before executing the code",
    "system_prompt": SUBAGENT_SYSTEM_PROMPT,
    "middleware": [],   # add FileSystemMiddleware later in coding_agent, to contain the currently uninitialized E2B backend
    "skills": ["/home/user/manim/"]
}