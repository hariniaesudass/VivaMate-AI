import streamlit as st
from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT
import time
import smtplib
from email.mime.text import MIMEText

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="VivaMate AI",
    page_icon="📚",
    layout="centered"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #666666;
        margin-bottom: 25px;
    }

    .feature-card {
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #dddddd;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">📚 VivaMate AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Your AI Study Assistant for Understanding and Viva Preparation'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# GEMINI CLIENT
# =========================================================

try:

    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )

    gemini_connected = True

except Exception:

    gemini_connected = False

    st.error(
        "Gemini API configuration is missing or invalid."
    )


# =========================================================
# SESSION STATE
# =========================================================

default_values = {

    "analysis": "",

    "question_answered": False,

    "viva_completed": False,

    "revision_downloaded": False,

    "quiz_started": False,

    "quiz_question": "",

    "quiz_feedback": "",

    "quiz_evaluated": False,

    "quiz_count": 0,

    "quiz_scores": [],

    "email_sent": False

}


for key, value in default_values.items():

    if key not in st.session_state:

        st.session_state[key] = value


# =========================================================
# GEMINI FUNCTION
# =========================================================

def generate_ai(contents):

    if not gemini_connected:

        return ""

    max_attempts = 3

    for attempt in range(max_attempts):

        try:

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=contents
            )

            return response.text

        except Exception as error:

            error_text = str(error)

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "high demand" in error_text.lower()
            ):

                if attempt < max_attempts - 1:

                    time.sleep(3)

                else:

                    st.error(
                        "⚠️ Gemini server is temporarily busy. "
                        "Please try again after some time."
                    )

            else:

                st.error(
                    "⚠️ Unable to get a response from Gemini."
                )

                st.caption(error_text)

                return ""

    return ""


# =========================================================
# RESET FUNCTION
# =========================================================

def reset_study():

    st.session_state.analysis = ""

    st.session_state.question_answered = False

    st.session_state.viva_completed = False

    st.session_state.revision_downloaded = False

    st.session_state.quiz_started = False

    st.session_state.quiz_question = ""

    st.session_state.quiz_feedback = ""

    st.session_state.quiz_evaluated = False

    st.session_state.quiz_count = 0

    st.session_state.quiz_scores = []

    st.session_state.email_sent = False


# =========================================================
# STUDENT INFORMATION
# =========================================================

st.subheader("👋 Welcome to VivaMate AI")

student_name = st.text_input(
    "Enter your name",
    placeholder="Example: Harini"
)


# =========================================================
# UPLOAD MATERIAL
# =========================================================

st.subheader("📖 Upload Your Study Material")

uploaded_file = st.file_uploader(
    "Upload notes, textbook page, diagram or study material",
    type=["jpg", "jpeg", "png"]
)


if uploaded_file:

    st.image(
        uploaded_file,
        caption="Uploaded Study Material",
        use_container_width=True
    )

    st.success(
        "Study material uploaded successfully! ✅"
    )


    # =====================================================
    # ANALYZE
    # =====================================================

    if st.button(
        "✨ Analyze Study Material",
        use_container_width=True
    ):

        if not student_name.strip():

            st.warning(
                "Please enter your name first."
            )

        else:

            with st.spinner(
                "🔍 Gemini is analyzing your study material..."
            ):

                image_bytes = uploaded_file.getvalue()

                analysis_prompt = """
Analyze the uploaded study material.

Give the response in the following structure:

1. Topic Identified
2. Simple Explanation
3. Important Points
4. Viva Questions with Short Answers
5. Quick Revision Notes

Rules:
- Use only information visible in the study material.
- Do not invent facts.
- Keep the explanation simple.
- Make it useful for a college student.
- Keep viva questions relevant to the uploaded material.
"""

                analysis = generate_ai(
                    [
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=uploaded_file.type
                        ),
                        SYSTEM_PROMPT,
                        analysis_prompt
                    ]
                )

            if analysis:

                st.session_state.analysis = analysis

                st.session_state.question_answered = False

                st.session_state.viva_completed = False

                st.session_state.revision_downloaded = False

                st.session_state.quiz_started = False

                st.session_state.quiz_question = ""

                st.session_state.quiz_feedback = ""

                st.session_state.quiz_evaluated = False

                st.session_state.quiz_count = 0

                st.session_state.quiz_scores = []


    # =====================================================
    # AI ANALYSIS
    # =====================================================

    if st.session_state.analysis:

        st.divider()

        st.subheader("📚 VivaMate Analysis")

        if student_name:

            st.write(
                "👋 Hello,",
                student_name
            )

        st.write(
            st.session_state.analysis
        )


        # =================================================
        # DOWNLOAD REVISION NOTES
        # =================================================

        st.divider()

        st.subheader("📝 Revision Notes")

        st.write(
            "Save your AI-generated revision material "
            "for quick exam preparation."
        )

        revision_download = st.download_button(
            "📥 Download Revision Notes",
            data=st.session_state.analysis,
            file_name="VivaMate_Revision_Notes.txt",
            mime="text/plain",
            use_container_width=True
        )

        if revision_download:

            st.session_state.revision_downloaded = True


        # =================================================
        # ASK VIVAMATE
        # =================================================

        st.divider()

        st.subheader("💬 Ask VivaMate")

        st.write(
            "Ask any question related to the uploaded "
            "study material."
        )

        question = st.text_input(
            "Your Question",
            placeholder="Example: What is the main concept?",
            key="question_input"
        )


        if st.button(
            "🤖 Ask VivaMate",
            use_container_width=True
        ):

            if not question.strip():

                st.warning(
                    "Please enter a question."
                )

            else:

                with st.spinner(
                    "🤖 VivaMate is thinking..."
                ):

                    image_bytes = uploaded_file.getvalue()

                    question_prompt = f"""
You are VivaMate AI.

Answer the student's question using ONLY
the uploaded study material.

Student Question:
{question}

Rules:
- Give a simple and clear answer.
- Do not invent information.
- If the answer is not available in the material,
  clearly say that it is not present.
- Keep the answer suitable for college exam preparation.
"""

                    answer = generate_ai(
                        [
                            types.Part.from_bytes(
                                data=image_bytes,
                                mime_type=uploaded_file.type
                            ),
                            question_prompt
                        ]
                    )

                if answer:

                    st.session_state.question_answered = True

                    st.subheader(
                        "💡 VivaMate Answer"
                    )

                    st.write(answer)


        # =================================================
        # VIVA PRACTICE
        # =================================================

        st.divider()

        st.subheader("🎤 Viva Practice")

        st.write(
            "Generate important viva questions "
            "from your uploaded study material."
        )


        if st.button(
            "🎯 Generate Viva Questions",
            use_container_width=True
        ):

            with st.spinner(
                "🎤 Preparing viva questions..."
            ):

                image_bytes = uploaded_file.getvalue()

                viva_prompt = """
Create 5 important viva questions from
the uploaded study material.

For every question provide:

Question:
Short Expected Answer:

Rules:
- Use only the uploaded material.
- Keep questions simple.
- Focus on important concepts.
- Make them suitable for college viva preparation.
"""

                viva_result = generate_ai(
                    [
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=uploaded_file.type
                        ),
                        viva_prompt
                    ]
                )

            if viva_result:

                st.session_state.viva_completed = True

                st.subheader(
                    "🎓 Viva Questions"
                )

                st.write(viva_result)


        # =================================================
        # INTERACTIVE VIVA QUIZ
        # =================================================

        st.divider()

        st.subheader("🧠 Interactive Viva Quiz")

        st.write(
            "Answer AI-generated viva questions "
            "and receive instant evaluation."
        )


        # -------------------------------------------------
        # START QUIZ
        # -------------------------------------------------

        if not st.session_state.quiz_started:

            if st.button(
                "🚀 Start Interactive Quiz",
                use_container_width=True
            ):

                with st.spinner(
                    "🧠 Generating your first question..."
                ):

                    quiz_prompt = f"""
You are VivaMate AI acting as a viva examiner.

Study Material:
{st.session_state.analysis}

Generate ONE important viva question.

Rules:
- Ask only one question.
- Do not give the answer.
- Question must be based only on the study material.
- Return only the question.
"""

                    first_question = generate_ai(
                        quiz_prompt
                    )

                if first_question:

                    st.session_state.quiz_question = first_question

                    st.session_state.quiz_started = True

                    st.session_state.quiz_evaluated = False

                    st.session_state.quiz_feedback = ""

                    st.session_state.quiz_count = 1

                    st.rerun()


        # -------------------------------------------------
        # ACTIVE QUIZ
        # -------------------------------------------------

        if st.session_state.quiz_started:

            st.info(
                "🎯 Viva Question "
                + str(st.session_state.quiz_count)
            )

            st.markdown(
                "**Question:**"
            )

            st.write(
                st.session_state.quiz_question
            )


            answer = st.text_area(
                "✍️ Your Answer",
                placeholder="Type your answer here...",
                height=130,
                key="quiz_answer_input"
            )


            # ---------------------------------------------
            # SUBMIT ANSWER
            # ---------------------------------------------

            if not st.session_state.quiz_evaluated:

                if st.button(
                    "✅ Submit Answer",
                    use_container_width=True
                ):

                    if not answer.strip():

                        st.warning(
                            "Please write your answer first."
                        )

                    else:

                        with st.spinner(
                            "📊 Evaluating your answer..."
                        ):

                            evaluation_prompt = f"""
You are a college viva examiner.

Study Material:
{st.session_state.analysis}

Question:
{st.session_state.quiz_question}

Student Answer:
{answer}

Evaluate the answer ONLY using the study material.

Return exactly this structure:

Score: X/10

Result:
Correct / Partially Correct / Needs Improvement

Feedback:
Short explanation of the student's answer.

Expected Answer:
Short ideal answer based only on the material.

Rules:
- Do not invent information.
- Be fair and concise.
- Focus on understanding rather than grammar.
"""

                            evaluation = generate_ai(
                                evaluation_prompt
                            )

                        if evaluation:

                            st.session_state.quiz_feedback = evaluation

                            st.session_state.quiz_evaluated = True

                            st.session_state.viva_completed = True

                            st.rerun()


            # ---------------------------------------------
            # SHOW EVALUATION
            # ---------------------------------------------

            if st.session_state.quiz_evaluated:

                st.divider()

                st.subheader(
                    "📊 Your Evaluation"
                )

                st.write(
                    st.session_state.quiz_feedback
                )


                # -----------------------------------------
                # NEXT QUESTION
                # -----------------------------------------

                if st.button(
                    "➡️ Next Viva Question",
                    use_container_width=True
                ):

                    with st.spinner(
                        "🧠 Preparing the next question..."
                    ):

                        next_question_prompt = f"""
You are VivaMate AI.

Study Material:
{st.session_state.analysis}

Previous Question:
{st.session_state.quiz_question}

Generate ONE different viva question.

Rules:
- Do not repeat the previous question.
- Use only information from the study material.
- Do not give the answer.
- Return only the question.
"""

                        next_question = generate_ai(
                            next_question_prompt
                        )

                    if next_question:

                        st.session_state.quiz_question = next_question

                        st.session_state.quiz_feedback = ""

                        st.session_state.quiz_evaluated = False

                        st.session_state.quiz_count += 1

                        st.rerun()


        # =================================================
        # SHARE / EMAIL
        # =================================================

        st.divider()

        st.subheader("📤 Share Revision Notes")

        st.write(
            "Send your revision notes to an email address."
        )

        recipient_email = st.text_input(
            "Recipient Email",
            placeholder="example@gmail.com"
        )


        if st.button(
            "📧 Send Revision Notes",
            use_container_width=True
        ):

            if not recipient_email.strip():

                st.warning(
                    "Please enter a recipient email."
                )

            elif "@" not in recipient_email:

                st.warning(
                    "Please enter a valid email address."
                )

            else:

                if (
                    "GMAIL_ADDRESS" in st.secrets
                    and "GMAIL_APP_PASSWORD" in st.secrets
                ):

                    try:

                        message = MIMEText(
                            st.session_state.analysis
                        )

                        message["Subject"] = (
                            "VivaMate AI - Revision Notes"
                        )

                        message["From"] = (
                            st.secrets["GMAIL_ADDRESS"]
                        )

                        message["To"] = recipient_email


                        with smtplib.SMTP_SSL(
                            "smtp.gmail.com",
                            465
                        ) as server:

                            server.login(
                                st.secrets["GMAIL_ADDRESS"],
                                st.secrets["GMAIL_APP_PASSWORD"]
                            )

                            server.send_message(
                                message
                            )


                        st.session_state.email_sent = True

                        st.success(
                            "📧 Revision notes sent successfully!"
                        )

                    except Exception as error:

                        st.error(
                            "Unable to send the email."
                        )

                        st.caption(
                            str(error)
                        )

                else:

                    st.info(
                        "Email sending is not configured yet. "
                        "Use the Download button above to save "
                        "your revision notes."
                    )


        # =================================================
        # STUDY PROGRESS
        # =================================================

        st.divider()

        st.subheader("📊 Your Study Progress")


        analysis_done = bool(
            st.session_state.analysis
        )

        question_done = (
            st.session_state.question_answered
        )

        viva_done = (
            st.session_state.viva_completed
        )

        download_done = (
            st.session_state.revision_downloaded
        )

        quiz_done = (
            st.session_state.quiz_evaluated
        )


        completed = 0

        if analysis_done:
            completed += 1

        if question_done:
            completed += 1

        if viva_done:
            completed += 1

        if download_done:
            completed += 1

        if quiz_done:
            completed += 1


        total_activities = 5

        progress = completed / total_activities


        st.progress(progress)

        st.write(
            "Progress: "
            + str(int(progress * 100))
            + "%"
        )


        if analysis_done:
            st.write("✅ AI Analysis Completed")
        else:
            st.write("⬜ AI Analysis")


        if question_done:
            st.write("✅ Asked VivaMate a Question")
        else:
            st.write("⬜ Ask VivaMate a Question")


        if viva_done:
            st.write("✅ Viva Practice Completed")
        else:
            st.write("⬜ Viva Practice")


        if download_done:
            st.write("✅ Revision Notes Downloaded")
        else:
            st.write("⬜ Download Revision Notes")


        if quiz_done:
            st.write("✅ Interactive Viva Quiz Completed")
        else:
            st.write("⬜ Interactive Viva Quiz")


        if progress == 1:

            st.success(
                "🎉 Excellent! You completed all "
                "VivaMate activities!"
            )


        # =================================================
        # START NEW STUDY
        # =================================================

        st.divider()

        st.subheader("🔄 Start New Study")

        st.write(
            "Finished with this topic? "
            "Start a fresh study session."
        )


        if st.button(
            "🆕 Start New Study",
            use_container_width=True
        ):

            reset_study()

            st.rerun()


else:

    # =====================================================
    # EMPTY STATE
    # =====================================================

    st.info(
        "👆 Upload your study material above "
        "to get started."
    )


    st.markdown(
        """
        ### 🌟 What VivaMate can do

        📷 **Analyze Study Material**

        💡 **Explain Difficult Concepts**

        💬 **Answer Your Questions**

        🎤 **Generate Viva Questions**

        🧠 **Conduct Interactive Viva**

        📊 **Evaluate Your Answers**

        📝 **Create Revision Notes**

        📥 **Download Your Notes**

        📧 **Share Notes by Email**

        📊 **Track Study Progress**
        """
    )