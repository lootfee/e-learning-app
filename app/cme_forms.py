from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectField, PasswordField, BooleanField, IntegerField, \
    DecimalField, FileField, HiddenField, TimeField, TextAreaField, RadioField, SelectMultipleField
from wtforms.fields.html5 import DateTimeLocalField
from wtforms.validators import DataRequired, InputRequired, ValidationError, EqualTo, Email
from flask_wtf.file import FileField
# from flask_pagedown.fields import PageDownField
# from app.models import User, Department, DocumentType, Document


def validate_select(form, field):
    if field.data == 0:
        raise ValidationError("Please select from choice list")


class EmployeeIdForm(FlaskForm):
    employee_id = StringField('Employee ID', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddTopicForm(FlaskForm):
    name = StringField('Topic Category', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddCourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired()])
    topic_id = SelectField('Topic category: ', coerce=int, validators=[DataRequired(), validate_select])
    cover_page = FileField('Cover Page', validators=[DataRequired()])
    presented_by1 = SelectField('Presented by: ', coerce=int, validators=[DataRequired(), validate_select])
    presented_by2 = SelectField('Presented by: (Optional)', coerce=int)
    presented_by3 = SelectField('Presented by: (Optional)', coerce=int)
    deadline = DateTimeLocalField('Deadline', validators=[DataRequired()], render_kw={"type": "datetime-local"},
                                           format='%Y-%m-%dT%H:%M')
    # presentation_date = DateTimeLocalField('Presentation Date', render_kw={"type": "datetime-local"}, format='%Y-%m-%dT%H:%M')
    # cme_points = IntegerField('CME Points')
    # cme_serial_no = IntegerField('CME Serial No.')
    submit = SubmitField('Save')


class EditCourseForm(FlaskForm):
    course_id = HiddenField('course_id', validators=[DataRequired()])
    title = StringField('Course Title', validators=[DataRequired()])
    topic_id = SelectField('Topic category: ', coerce=int, validators=[DataRequired(), validate_select])
    cover_page = FileField('Cover Page(leave blank if unchanged)')
    presented_by1 = SelectField('Presented by: ', coerce=int, validators=[DataRequired(), validate_select])
    presented_by2 = SelectField('Presented by: (Optional)', coerce=int)
    presented_by3 = SelectField('Presented by: (Optional)', coerce=int)
    deadline = DateTimeLocalField('Deadline', render_kw={"type": "datetime-local"},
                                  format='%Y-%m-%dT%H:%M')
    # presentation_date = DateTimeLocalField('Presentation Date', render_kw={"type": "datetime-local"}, format='%Y-%m-%dT%H:%M')
    submit = SubmitField('Save')


class PublishCertificateForm(FlaskForm):
    cert_course_id = HiddenField('course_id', validators=[DataRequired()])
    cme_points = IntegerField('CME Points')
    cme_serial_no = StringField('CME Serial No.')
    cert_submit = SubmitField('Publish')


class AddCourseContentForm(FlaskForm):
    index = IntegerField('Index', validators=[DataRequired()])
    title = StringField('Content Title', validators=[DataRequired()])
    submit = SubmitField('Save')


class EditCourseContentForm(FlaskForm):
    content_id = HiddenField('content_id', validators=[DataRequired()])
    edit_index = IntegerField('Index', validators=[DataRequired()])
    edit_title = StringField('Content Title', validators=[DataRequired()])
    edit_submit = SubmitField('Save')


class AddContentSlideForm(FlaskForm):
    index = IntegerField('Index', validators=[DataRequired()])
    image_file = FileField('Slide Image', validators=[DataRequired()])
    slide_text = TextAreaField('Slide Text', validators=[DataRequired()])
    submit = SubmitField('Save')


class AddContentVideoForm(FlaskForm):
    video_index = IntegerField('Index', validators=[DataRequired()])
    video_file = FileField('Video File', validators=[DataRequired()])
    video_submit = SubmitField('Save')


class EditContentSlideForm(FlaskForm):
    slide_id = HiddenField('slide_id', validators=[DataRequired()])
    edit_index = IntegerField('Index', validators=[DataRequired()])
    edit_image_file = FileField('Slide Image(Leave blank if unchanged)')
    edit_slide_text = TextAreaField('Slide Text', validators=[DataRequired()])
    edit_submit = SubmitField('Save')


class AddQuestionForm(FlaskForm):
    question = StringField('Question', validators=[DataRequired()])
    #image_file = FileField('Add Image(Optional)')
    answer_explanation = StringField('Answer Explanation')
    submit = SubmitField('Save')


class EditQuestionForm(FlaskForm):
    question_id = HiddenField('question_id', validators=[DataRequired()])
    edit_question = StringField('Question', validators=[DataRequired()])
    #image_file = FileField('Add Image(Optional)')
    edit_answer_explanation = StringField('Answer Explanation')
    edit_submit = SubmitField('Save')


class CourseQuestionForm(FlaskForm):
    question = TextAreaField('Question', validators=[DataRequired()])
    submit = SubmitField('Submit')


class CourseQuestionAnswerForm(FlaskForm):
    question_id = HiddenField('question_id', validators=[DataRequired()])
    answer = TextAreaField('Answer', validators=[DataRequired()])
    submit = SubmitField('Submit')


class CourseReviewForm(FlaskForm):
    q1 = SelectField('1. The objectives of the training were clearly defined.',
                     choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'), (1, 'Strongly disagree')],
                     validators=[InputRequired()])
    q2 = SelectField('2. The knowledge I gained will help me in optimizing my work processes and my professional competence.',
                     choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                              (1, 'Strongly disagree')],
                     validators=[InputRequired()])
    q3 = SelectField(
        '3. The information was presented at an appropriate learning level for this stage in my career.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q4 = SelectField(
        '4. The training provided me with new idea and resources.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q5 = SelectField(
        '5. I would recommend this training to my colleagues.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q6 = SelectField(
        '6. The venue was appropriate for the training.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q7 = SelectField(
        '7. The objectives of the training were met.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q8 = SelectField(
        '8. The content of the course was organized and easy to follow.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q9 = SelectField(
        '9. Projection quality (appropriate letter size and color).',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q10 = SelectField(
        '10. The presentation materials were relevant and readable (amount of material/visuals).',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q11 = SelectField(
        '11. The presentation was concise and informative.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q12 = SelectField(
        '12. The presentation contained practical examples and useful techniques which could be applied to everyday work.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q13 = SelectField(
        '13. The presenter demonstrated substantive knowledge of the topic.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q14 = SelectField(
        '14. The presenter effectively links the different sections of the talk.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q15 = SelectField(
        '15. The presenter was engaging.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q16 = SelectField(
        '16. The trainer was well prepared and able to answer any questions.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q17 = SelectField(
        '17. The presenter uses appropriate pitch, flexibility, and volume of voice.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q18 = SelectField(
        '18. The presenter uses understandable language pronunciation .',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q19 = SelectField(
        '19. The presenter has strong presentation and delivery style.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q20 = SelectField(
        '20. The pre and post program questions are fair to evaluate my understanding of the program.',
        choices=[(5, 'Strongly agree'), (4, 'Agree'), (3, 'Neutral'), (2, 'Disagree'),
                 (1, 'Strongly disagree')],
        validators=[InputRequired()])
    q21 = TextAreaField('1.	What did you like about the CME/training event?')
    q22 = TextAreaField('2.	2)	What other training topics would you like to attend?')

    submit = SubmitField('Submit')