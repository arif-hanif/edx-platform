"""
Test capa problem.
"""
import ddt
import textwrap
from lxml import etree
import unittest

from . import new_loncapa_problem


@ddt.ddt
class CAPAProblemTest(unittest.TestCase):
    """ CAPA problem related tests"""

    def test_label_and_description_inside_responsetype(self):
        """
        Verify that
        * label is extracted
        * <label> tag is removed to avoid duplication

        This is the case when we have a problem with single question or
        problem with multiple-questions separated as per the new format.
        """
        xml = """
        <problem>
            <choiceresponse>
                <label>Select the correct synonym of paranoid?</label>
                <description>Only the paranoid survive.</description>
                <checkboxgroup>
                    <choice correct="true">over-suspicious</choice>
                    <choice correct="false">funny</choice>
                </checkboxgroup>
            </choiceresponse>
        </problem>
        """
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2_1':
                {
                    'label': 'Select the correct synonym of paranoid?',
                    'descriptions': {'description_1_1_1': 'Only the paranoid survive.'}
                }
            }
        )
        self.assertEqual(len(problem.tree.xpath('//label')), 0)

    def test_legacy_problem(self):
        """
        Verify that legacy problem is handled correctly.
        """
        question = "Once we become predictable, we become ______?"
        xml = """
        <problem>
            <p>Be sure to check your spelling.</p>
            <p>{}</p>
            <stringresponse answer="vulnerable" type="ci">
                <textline label="{}" size="40"/>
            </stringresponse>
        </problem>
        """.format(question, question)
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2_1':
                {
                    'label': question,
                    'descriptions': {}
                }
            }
        )
        self.assertEqual(
            len(problem.tree.xpath("//*[normalize-space(text())='{}']".format(question))),
            0
        )

    def test_neither_label_tag_nor_attribute(self):
        """
        Verify that label is extracted correctly.

        This is the case when we have a markdown problem with multiple-questions.
        In this case when markdown is converted to xml, there will be no label
        tag and label attribute inside responsetype. But we have a label tag
        before the responsetype.
        """
        question1 = 'People who say they have nothing to ____ almost always do?'
        question2 = 'Select the correct synonym of paranoid?'
        xml = """
        <problem>
            <p>Be sure to check your spelling.</p>
            <label>{}</label>
            <stringresponse answer="hide" type="ci">
                <textline size="40"/>
            </stringresponse>
            <choiceresponse>
                <label>{}</label>
                <checkboxgroup>
                    <choice correct="true">over-suspicious</choice>
                    <choice correct="false">funny</choice>
                </checkboxgroup>
            </choiceresponse>
        </problem>
        """.format(question1, question2)
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2_1':
                {
                    'label': question1,
                    'descriptions': {}
                },
                '1_3_1':
                {
                    'label': question2,
                    'descriptions': {}
                }
            }

        )
        for question in (question1, question2):
            self.assertEqual(
                len(problem.tree.xpath('//label[text()="{}"]'.format(question))),
                0
            )

    def test_multiple_descriptions(self):
        """
        Verify that multiple descriptions are handled correctly.
        """
        xml = """
        <problem>
            <p>Be sure to check your spelling.</p>
            <stringresponse answer="War" type="ci">
                <label>___ requires sacrifices.</label>
                <description>The problem with trying to be the bad guy, there's always someone worse.</description>
                <description>Anyone who looks the world as if it was a game of chess deserves to lose.</description>
                <textline size="40"/>
            </stringresponse>
        </problem>
        """
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2_1':
                {
                    'label': '___ requires sacrifices.',
                    'descriptions': {
                        'description_1_1_1': "The problem with trying to be the bad guy, there's always someone worse.",
                        'description_1_1_2': "Anyone who looks the world as if it was a game of chess deserves to lose."
                    }
                }
            }
        )

    def test_non_accessible_inputtype(self):
        """
        Verify that tag with question text is not removed when inputtype is not fully accessible.
        """
        question = "Click the country which is home to the Pyramids."
        xml = """
        <problem>
            <p>{}</p>
            <imageresponse>
                <imageinput label="{}"
                src="/static/Africa.png" width="600" height="638" rectangle="(338,98)-(412,168)"/>
            </imageresponse>
        </problem>
        """.format(question, question)
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2_1':
                {
                    'label': question,
                    'descriptions': {}
                }
            }
        )
        # <p> tag with question text should not be deleted
        self.assertEqual(problem.tree.xpath("string(p[text()='{}'])".format(question)), question)

    def test_label_is_empty_if_no_label_attribute(self):
        """
        Verify that label in response_data is empty string when label
        attribute is missing and responsetype is not fully accessible.
        """
        question = "Click the country which is home to the Pyramids."
        xml = """
        <problem>
            <p>{}</p>
            <imageresponse>
                <imageinput
                src="/static/Africa.png" width="600" height="638" rectangle="(338,98)-(412,168)"/>
            </imageresponse>
        </problem>
        """.format(question)
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2_1':
                {
                    'label': '',
                    'descriptions': {}
                }
            }
        )

    def test_multiple_questions_problem(self):
        """
        For a problem with multiple questions verify that for each question
        * label is extracted
        * descriptions info is constructed
        * <label> tag is removed to avoid duplication
        """
        xml = """
        <problem>
            <choiceresponse>
                <label>Select the correct synonym of paranoid?</label>
                <description>Only the paranoid survive.</description>
                <checkboxgroup>
                    <choice correct="true">over-suspicious</choice>
                    <choice correct="false">funny</choice>
                </checkboxgroup>
            </choiceresponse>
            <multiplechoiceresponse>
                <p>one more question</p>
                <label>What Apple device competed with the portable CD player?</label>
                <description>Device looks like an egg plant.</description>
                <choicegroup type="MultipleChoice">
                    <choice correct="false">The iPad</choice>
                    <choice correct="false">Napster</choice>
                    <choice correct="true">The iPod</choice>
                    <choice correct="false">The vegetable peeler</choice>
                </choicegroup>
            </multiplechoiceresponse>
        </problem>
        """
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2_1':
                {
                    'label': 'Select the correct synonym of paranoid?',
                    'descriptions': {'description_1_1_1': 'Only the paranoid survive.'}
                },
                '1_3_1':
                {
                    'label': 'What Apple device competed with the portable CD player?',
                    'descriptions': {'description_1_2_1': 'Device looks like an egg plant.'}
                }
            }
        )
        self.assertEqual(len(problem.tree.xpath('//label')), 0)

    def test_question_title_not_removed_got_children(self):
        """
        Verify that <p> question text before responsetype not deleted when
        it contains other children and label is picked from label attribute of inputtype

        This is the case when author updated the <p> immediately before
        responsetype to contain other elements. We do not want to delete information in that case.
        """
        question = 'Is egg plant a fruit?'
        xml = """
        <problem>
            <p>Choose wisely.</p>
            <p>Select the correct synonym of paranoid?</p>
            <p><img src="" /></p>
            <choiceresponse>
                <checkboxgroup label="{}">
                    <choice correct="true">over-suspicious</choice>
                    <choice correct="false">funny</choice>
                </checkboxgroup>
            </choiceresponse>
        </problem>
        """.format(question)
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2_1':
                {
                    'label': '',
                    'descriptions': {}
                }
            }
        )
        self.assertEqual(
            len(problem.tree.xpath('//p/img')),
            1
        )

    def test_multiple_inputtypes(self):
        """
        Verify that group label and labels for individual inputtypes are extracted correctly.
        """
        group_label = 'Choose the correct color'
        input1_label = 'What color is the sky?'
        input2_label = 'What color are pine needles?'
        xml = """
        <problem>
            <optionresponse>
                <label>{}</label>
                <optioninput options="('yellow','blue','green')" correct="blue" label="{}"/>
                <optioninput options="('yellow','blue','green')" correct="green" label="{}"/>
            </optionresponse>
        </problem>
        """.format(group_label, input1_label, input2_label)

        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2_1':
                {
                    'group_label': group_label,
                    'label': input1_label,
                    'descriptions': {}
                },
                '1_2_2':
                {
                    'group_label': group_label,
                    'label': input2_label,
                    'descriptions': {}
                }
            }
        )

    def test_single_inputtypes(self):
        """
        Verify that HTML is correctly rendered when there is single inputtype.
        """
        question = 'Enter sum of 1+2'
        xml = textwrap.dedent("""
        <problem>
            <customresponse cfn="test_sum" expect="3">
        <script type="loncapa/python">
        def test_sum(expect, ans):
            return int(expect) == int(ans)
        </script>
                <label>{}</label>
                <textline size="20" correct_answer="3" />
            </customresponse>
        </problem>
        """.format(question))
        problem = new_loncapa_problem(xml, use_capa_render_template=True)
        problem_html = etree.XML(problem.get_html())

        # verify that only no multi input group div is present
        multi_inputs_group = problem_html.xpath('//div[@class="multi-inputs-group"]')
        self.assertEqual(len(multi_inputs_group), 0)

        # verify that question is rendered only once
        question = problem_html.xpath("//*[normalize-space(text())='{}']".format(question))
        self.assertEqual(len(question), 1)

    def assert_question_tag(self, question1, question2, tag, label_attr=False):
        """
        Verify question tag correctness.
        """
        question1_tag = '<{tag}>{}</{tag}>'.format(question1, tag=tag) if question1 else ''
        question2_tag = '<{tag}>{}</{tag}>'.format(question2, tag=tag) if question2 else ''
        question1_label_attr = 'label="{}"'.format(question1) if label_attr else ''
        question2_label_attr = 'label="{}"'.format(question2) if label_attr else ''
        xml = """
        <problem>
            {question1_tag}
            <choiceresponse>
                <checkboxgroup {question1_label_attr}>
                    <choice correct="true">choice1</choice>
                    <choice correct="false">choice2</choice>
                </checkboxgroup>
            </choiceresponse>
            {question2_tag}
            <multiplechoiceresponse>
                <choicegroup type="MultipleChoice" {question2_label_attr}>
                    <choice correct="false">choice1</choice>
                    <choice correct="true">choice2</choice>
                </choicegroup>
            </multiplechoiceresponse>
        </problem>
        """.format(
            question1_tag=question1_tag,
            question2_tag=question2_tag,
            question1_label_attr=question1_label_attr,
            question2_label_attr=question2_label_attr,
        )
        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2_1':
                {
                    'label': question1,
                    'descriptions': {}
                },
                '1_3_1':
                {
                    'label': question2,
                    'descriptions': {}
                }
            }
        )
        self.assertEqual(len(problem.tree.xpath('//{}'.format(tag))), 0)

    @ddt.unpack
    @ddt.data(
        {'question1': 'question 1 label', 'question2': 'question 2 label'},
        {'question1': '', 'question2': 'question 2 label'},
        {'question1': 'question 1 label', 'question2': ''}
    )
    def test_correct_question_tag_is_picked(self, question1, question2):
        """
        For a problem with multiple questions verify that correct question tag is picked.
        """
        self.assert_question_tag(question1, question2, tag='label', label_attr=False)
        self.assert_question_tag(question1, question2, tag='p', label_attr=True)

    def test_question_tag_child_left(self):
        """
        If the "old" question tag has children, don't delete the children when
        transforming to the new label tag.
        """
        xml = """
            <problem>
                <p>Question<img src='img/src'/></p>
                <choiceresponse>
                    <checkboxgroup label="Question">
                        <choice correct="true">choice1</choice>
                        <choice correct="false">choice2</choice>
                    </checkboxgroup>
                </choiceresponse>
            </problem>
            """

        problem = new_loncapa_problem(xml)
        self.assertEqual(
            problem.problem_data,
            {
                '1_2_1':
                    {
                        'label': "Question",
                        'descriptions': {}
                    }
            }
        )
        # img tag is still present within the paragraph, but p text has been deleted
        self.assertEqual(len(problem.tree.xpath('//p')), 1)
        self.assertEqual(problem.tree.xpath('//p')[0].text, '')
        self.assertEqual(len(problem.tree.xpath('//p/img')), 1)


@ddt.ddt
class CAPAMultiInputProblemTest(unittest.TestCase):
    """ TestCase for CAPA problems with multiple inputtypes """

    def capa_problem(self, xml):
        """
        Create capa problem.
        """
        return new_loncapa_problem(xml, use_capa_render_template=True)

    def assert_problem_html(self, problme_html, group_label, *input_labels):
        """
        Verify that correct html is rendered for multiple inputtypes.
        """
        html = etree.XML(problme_html)

        # verify that only one multi input group div is present at correct path
        multi_inputs_group = html.xpath(
            '//section[@class="wrapper-problem-response"]/div[@class="multi-inputs-group"]'
        )
        self.assertEqual(len(multi_inputs_group), 1)

        # verify that multi input group label <p> tag exists and its
        # id matches with correct multi input group aria-labelledby
        multi_inputs_group_label_id = multi_inputs_group[0].attrib.get('aria-labelledby')
        multi_inputs_group_label = html.xpath('//p[@id="{}"]'.format(multi_inputs_group_label_id))
        self.assertEqual(len(multi_inputs_group_label), 1)
        self.assertEqual(multi_inputs_group_label[0].text, group_label)

        # verify that label for each input comes only once
        for input_label in input_labels:
            # normalize-space is used to remove whitespace around the text
            input_label_element = multi_inputs_group[0].xpath('//*[normalize-space(text())="{}"]'.format(input_label))
            self.assertEqual(len(input_label_element), 1)

    def test_optionresponse(self):
        """
        Verify that optionresponse problem with multiple inputtypes is rendered correctly.
        """
        group_label = 'Choose the correct color'
        input1_label = 'What color is the sky?'
        input2_label = 'What color are pine needles?'
        xml = """
        <problem>
            <optionresponse>
                <label>{}</label>
                <optioninput options="('yellow','blue','green')" correct="blue" label="{}"/>
                <optioninput options="('yellow','blue','green')" correct="green" label="{}"/>
            </optionresponse>
        </problem>
        """.format(group_label, input1_label, input2_label)
        problem = self.capa_problem(xml)
        self.assert_problem_html(problem.get_html(), group_label, input1_label, input2_label)

    @ddt.unpack
    @ddt.data(
        {'inputtype': 'textline'},
        {'inputtype': 'formulaequationinput'}
    )
    def test_customresponse(self, inputtype):
        """
        Verify that customresponse problem with multiple textline
        and formulaequationinput inputtypes is rendered correctly.
        """
        group_label = 'Enter two integers that sum to 10.'
        input1_label = 'Integer 1'
        input2_label = 'Integer 2'
        xml = textwrap.dedent("""
        <problem>
            <customresponse cfn="test_add_to_ten">
        <script type="loncapa/python">
        def test_add_to_ten(expect, ans):
            return test_add(10, ans)
        </script>
                <label>{}</label>
                <{inputtype} size="40" correct_answer="3" label="{}" /><br/>
                <{inputtype} size="40" correct_answer="7" label="{}" />
            </customresponse>
        </problem>
        """.format(group_label, input1_label, input2_label, inputtype=inputtype))
        problem = self.capa_problem(xml)
        self.assert_problem_html(problem.get_html(), group_label, input1_label, input2_label)
