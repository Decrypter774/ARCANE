import json


class TestPromptBuilder:
    @staticmethod
    def build_multiple_choice_prompt(topic, additional_context="", language="english", number_of_questions=5,
                                     user_profile=None, lesson_content_context=""):
        user_context_string = ""
        if user_profile:
            if user_profile.get('age'):
                user_context_string += f" The user is {user_profile.get('age')} years old."
            if user_profile.get('bio'):
                user_context_string += f" The user's bio: '{user_profile.get('bio')}'."
            if user_context_string:
                user_context_string = f"Consider the following user profile when creating questions:{user_context_string}"

        lesson_context_string = ""
        if lesson_content_context:
            lesson_context_string = f"""
            IMPORTANT: The following is the content of the lessons from this unit. You MUST base your questions directly on this material.
            --- LESSON CONTENT START ---
            {lesson_content_context}
            --- LESSON CONTENT END ---
            """

        return f"""
            You are creating a test on the topic: {topic}.
            {additional_context}
            {user_context_string}
            {lesson_context_string}

            Create {number_of_questions} multiple choice questions.

            IMPORTANT CONSTRAINTS:
            - Each question must have EXACTLY ONE correct answer
            - Do NOT create questions where multiple options are correct (e.g., "Which of the following are true: 1,2,4")
            - Do NOT create questions asking to "select all that apply"
            - Each question should have 4 options with only 1 being correct
            - Make sure the incorrect options are plausible but clearly wrong
            Your entire response MUST be a valid JSON object.
            Generate the response in the following language: {language}.
            All user-visible string values (like test-name, topic, question, and option text) must be in {language}.
            Keep all JSON keys (like "test-name", "topic", "questions", "type", "options", "option1", etc.) in English.

            Use this format:

            {{
              "test-name": "Sample Test Name",
              "topic": "{topic}",
              "questions": [
                {{
                  "question": "Sample question text?",
                  "type": "single-answer",
                  "options": {{
                    "option1": "Answer A",
                    "option2": "Answer B",
                    "option3": "Answer C",
                    "option4": "Answer D"
                  }}
                }}
              ]
            }}
        """

    @staticmethod
    def build_open_question_prompt(topic, additional_prompt="", language="english"):
        return f"""
            Create 10-15 open-ended questions to assess someone's knowledge on "{topic}".
            {additional_prompt}

            Your entire response MUST be a valid JSON object.
            Generate the response in the following language: {language}.
            All user-visible string values (like test-name, topic, and question text) must be in {language}.
            Keep all JSON keys (like "test-name", "topic", "questions", "type") in English.

            Respond in this JSON format:

            {{
              "test-name": "Open Test",
              "topic": "{topic}",
              "questions": [
                {{
                  "question": "Explain how XYZ works...",
                  "type": "open-ended"
                }}
              ]
            }}
        """


class AnswerPromptBuilder:
    @staticmethod
    def build_batch_check_prompt(questions_and_answers, language="english"):
        """
        Builds a prompt to check all answers in a single API call.
        """
        qa_string = ""
        for i, qa in enumerate(questions_and_answers):
            qa_string += f"""
            {{
                "id": {i},
                "question": "{qa['question']}",
                "user_answer": "{qa['answer']}"
            }}
            """

        return f"""
            You are an expert evaluator. Below is a list of questions and the user's answers.
            For each question, reply with "correct" or "incorrect" and then provide a brief, one-sentence explanation for your reasoning in {language}.

            Evaluate the following items:
            {qa_string}

            Your entire response MUST be a valid JSON object.
            The JSON object should have a single key "assessments", which is an array.
            Each object in the array must contain the "id" of the question and the "assessment" string.
            The order of the assessments in the array MUST match the order of the questions provided.

            Example format:
            {{
                "assessments": [
                    {{
                        "id": 0,
                        "assessment": "correct. Your explanation was spot on."
                    }},
                    {{
                        "id": 1,
                        "assessment": "incorrect. This is actually caused by..."
                    }}
                ]
            }}
        """

    @staticmethod
    def build_check_prompt(question, answer, options, isopen, language="english"):
        if isopen:
            return (
                f'Reply with "correct" or "incorrect" in {language}. Then, briefly explain your reasoning in {language}.\n'
                f'Question: {question}\n'
                f'User\'s Answer: {answer}?\n'
            )
        else:
            return (
                f'Reply with "correct" or "incorrect" in {language}. Then, briefly explain your reasoning in {language}.\n'
                f'Question: {question}\n'
                f'Options: {str(options)}'
                f'User\'s Answer: {answer}?\n'
            )


class CoursePromptBuilder:
    @staticmethod
    def build_course_structure_prompt(topic, knowledge_assessment, assessed_answers, language="english",
                                      lesson_duration=15, user_profile=None):
        assessed_answers_string = "\n".join([
            f"Q: {item['question']}\nA: {item['answer']}\nAssessment: {item['assessment']}\n"
            for item in assessed_answers
        ])

        user_context_string = ""
        if user_profile:
            profile_details = []
            if user_profile.get('age'):
                profile_details.append(f"Age: {user_profile.get('age')}")
            if user_profile.get('bio'):
                profile_details.append(f"Bio: '{user_profile.get('bio')}'")
            if profile_details:
                user_context_string = f"- Personalize the course for the following user profile: {'; '.join(profile_details)}."

        return f"""
            A learner has completed a test on the topic: "{topic}".
            Here is a qualitative assessment of their knowledge based on the test:
            "{knowledge_assessment}"

            Below is a detailed breakdown of their responses:
            {assessed_answers_string}

            Your task:
            - Based on their performance and the overall assessment, design a personalized course outline to help them improve.
            {user_context_string}
            - The course should include units. Each unit should contain lessons (with estimated completion time in minutes) and a test.
            - Do NOT generate lesson or test content yet—only the structure.
            - Lessons should be appropriately sequenced for progressive learning.
            - Your entire response MUST be a valid JSON object.
            - Generate the user-visible string values in the JSON (like course_title, unit_title, lesson_title, test_title) in the following language: {language}.
            - Keep all JSON keys (like "course_title", "units", "lessons", "estimated_time_minutes", "test", "test_title") in English.


            Return the course structure using the format:

            {{
              "course_title": "{topic}",
              "units": [
                {{
                  "unit_title": "Unit 1: Foundations of {topic}",
                  "lessons": [
                    {{
                      "lesson_title": "Lesson 1.1: Basics of XYZ",
                      "estimated_time_minutes": {lesson_duration}
                    }}
                  ],
                  "test": {{
                    "test_title": "Unit 1 Assessment"
                  }}
                }}
              ]
            }}
        """


class ChatPromptBuilder:
    @staticmethod
    def build_chat_prompt(lesson_content, unit_title, chat_history, user_question, language="english"):
        """
        Builds a prompt for the AI tutor to respond to user questions in the context of a lesson.
        
        Args:
            lesson_content (str): The content of the current lesson
            unit_title (str): Title of the unit the lesson belongs to
            chat_history (list): List of previous messages in the format [{"role": "user"|"assistant", "content": "message"}]
            user_question (str): The user's question
            language (str): Language for the response
            
        Returns:
            str: Formatted prompt for the AI tutor
        """
        # Format chat history
        history_text = ""
        if chat_history:
            history_text = "\nPrevious conversation:\n"
            for msg in chat_history[-5:]:  # Only include last 5 exchanges for context
                role = "Student" if msg["role"] == "user" else "Tutor"
                history_text += f"{role}: {msg['content']}\n"

        return f"""
        You are an AI tutor helping a student learn about {unit_title}.
        
        Here is the relevant lesson content:
        --- LESSON CONTENT START ---
        {lesson_content}
        --- LESSON CONTENT END ---
        
        {history_text}
        
        Student's question: {user_question}
        
        Please provide a helpful, clear, and concise response to the student's question.
        - If the question is off-topic, gently guide the conversation back to the lesson.
        - If you don't know the answer, say so rather than making up information.
        - Keep your response focused and educational.
        - Respond in {language}.
        """


class CourseEditorPromptBuilder:
    @staticmethod
    def build_edit_prompt(current_course_json, user_request, language="english"):
        """
        Builds a prompt for editing an existing course structure.
        
        Args:
            current_course_json (dict): Current course structure in JSON format
            user_request (str): User's edit request/instructions
            language (str): Language for the response
            
        Returns:
            str: Formatted prompt for editing the course
        """
        return f"""
        You are an AI course editor. Your task is to modify the existing course structure based on the user's request.
        
        CURRENT COURSE STRUCTURE:
        {json.dumps(current_course_json, indent=2)}
        
        USER REQUEST:
        {user_request}
        
        INSTRUCTIONS:
        1. Make the minimal necessary changes to satisfy the user's request
        2. Maintain the existing structure and format
        3. Keep all existing content unless explicitly asked to remove it
        4. Ensure the course remains logically structured
        5. If adding new content, make it consistent with the existing style
        6. Return the complete updated course structure in valid JSON format
        7. Respond in {language}
        
        Return ONLY the updated JSON structure, with no additional text or explanation.
        """
        
    @staticmethod
    def build_title_improvement_prompt(user_request, language="english"):
        """
        Builds a prompt for improving or updating a course title based on user input.
        
        Args:
            user_request (str): User's request for title change/improvement
            language (str): Language for the response
            
        Returns:
            str: Formatted prompt for generating an improved course title
        """
        return f"""
        You are an AI course title generator. The user wants to update their course title.
        
        USER REQUEST:
        {user_request}
        
        INSTRUCTIONS:
        1. Generate a single, concise, and engaging course title based on the user's request
        2. The title should be clear, informative, and appealing to potential students
        3. Keep it under 60 characters if possible
        4. Do not include any explanations, just return the title
        5. Respond in {language}
        
        Return ONLY the new course title, with no additional text or quotation marks.
        """


class LessonPromptBuilder:
    @staticmethod
    def build_lesson_content_prompt(lesson_title, unit_title, language="english", lesson_duration=15, user_profile=None,
                                    course_structure=None):
        user_context_string = ""
        if user_profile:
            profile_details = []
            if user_profile.get('age'):
                profile_details.append(f"Age: {user_profile.get('age')}")
            if user_profile.get('bio'):
                profile_details.append(f"Bio: '{user_profile.get('bio')}'")
            if profile_details:
                user_context_string = f"- Personalize the tone, examples, and analogies for the user. User profile: {'; '.join(profile_details)}. For instance, if their bio mentions programming, use technical analogies."

        course_context_string = ""
        if course_structure:
            course_context_string = f"""
            For context, here is the full structure of the course this lesson is a part of. This can help you reference other lessons if needed.
            --- COURSE STRUCTURE START ---
            {json.dumps(course_structure, indent=2)}
            --- COURSE STRUCTURE END ---
            """

        return f"""
            You are an expert AI tutor.

            Generate a comprehensive, structured, and beginner-friendly lesson on the topic: "{lesson_title}".
            This lesson is part of the unit: "{unit_title}".
            The entire lesson content MUST be in {language}.
            {course_context_string}

            Guidelines:
            - Use clear Markdown formatting (## Headings, bullet points, code blocks if needed).
            - Include step-by-step explanations, illustrative examples, and analogies.
            - The lesson's length MUST be calibrated for a {lesson_duration}-minute completion time for an average student. A shorter duration means a more concise, high-level overview. A longer duration allows for more depth, detail, and examples.
            - Use concise, easy-to-understand language for learners at various levels.
            {user_context_string}"""+"""

            Mathematical Formulas:
            - For inline mathematical expressions, wrap them in single dollar signs, like `$\frac{1}{2}$`.
            - For display-style equations (on their own line), wrap them in double dollar signs, like `$$\sum_{i=1}^{n} i = \frac{n(n + 1)}{2}$$`.
            - Use standard LaTeX syntax for all mathematical formulas.

            Visual Aids:
            - Insert AI image placeholders only when the visual would enhance understanding.
            - All images must follow this format exactly:
              [IMAGE_PROMPT: "A grayscale, schematic-style diagram with no text, showing ..."]

            Example:
            [IMAGE_PROMPT: "A grayscale, schematic-style diagram with no text, showing the layers of a neural network"]

            IMPORTANT: Do NOT include any text in the images themselves, as the AI image generator struggles with rendering text in images. I want the images to be a grayscale, schematic diagram.

            The lesson should be clear, logically organized, and visually supported where appropriate.
        """

        class ChatPromptBuilder:
            @staticmethod
            def build_tutor_prompt(lesson_content, unit_title, chat_history, user_question, language="english"):
                # Format the chat history for the prompt
                history_string = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])

                return f"""
            You are a friendly and encouraging AI tutor named Quillio.
            Your goal is to help a student understand a specific lesson. You have perfect knowledge of the lesson content provided below.
            You must only answer questions related to the lesson's topic. If asked about something unrelated, politely steer the conversation back to the lesson.
            Keep your answers concise and easy to understand.
            Your entire response MUST be in the following language: {language}.

            CONTEXT:
            - The student is studying the unit: "{unit_title}"
            - The student is viewing a lesson with the following content (this is the ground truth):
            --- LESSON CONTENT START ---
            {lesson_content}
            --- LESSON CONTENT END ---

            - Here is the conversation so far:
            --- CHAT HISTORY START ---
            {history_string}
            --- CHAT HISTORY END ---

            Now, answer the student's latest question based on the provided lesson content (no markdown please).
            Student's Question: "{user_question}"
        """

        class CourseEditorPromptBuilder:
            @staticmethod
            def build_title_improvement_prompt(current_title, language="english"):
                """Generate a prompt to improve the course title."""
                return f"Please make this name for a course more concise and engaging: {current_title}"

            @staticmethod
            def build_edit_prompt(current_course_json, user_request, language="english"):
                # Check if this is a title update request
                title_keywords = ["title", "name", "rename", "call this"]
                is_title_update = any(keyword in user_request.lower() for keyword in title_keywords)

                # If it's a title update, use the fast model for just the title
                if is_title_update and "course_title" in current_course_json:
                    return {
                        "course_title": user_request,
                        "units": current_course_json.get("units", [])
                    }

                course_str = json.dumps(current_course_json, indent=2)

                return f"""
            You are an expert AI curriculum editor. Your task is to modify a course structure, which is provided as a JSON object.
            The user will give you a command in plain text. You must interpret this command and apply it to the JSON structure.

            IMPORTANT RULES:
            1. Your entire response MUST be only the new, complete, and valid JSON object for the entire course.
            2. Do NOT add any extra text, explanations, or markdown formatting around the JSON.
            3. The structure of the JSON (keys like "course_title", "units", "lessons", "test") must be preserved.
            4. If you add new lessons, ensure they have an "estimated_time_minutes" key.
            5. All user-visible strings in the JSON (titles) must be in the following language: {language}.

            Here is the current course structure:
            {course_str}

            Here is the user's request:
            "{user_request}"

            Now, return the complete, modified JSON object reflecting the user's request.
        """