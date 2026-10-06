from random import randint
from os.path import join
from json import dump
from argparse import ArgumentParser


parse = ArgumentParser()
parse.add_argument("-l", "--lenques", type=int, default=500, help="整数值,要生成的题目数量,默认500")
parse.add_argument("-c", "--choratid", type=float, default=0.6, help="浮点值,多选题的生成比例,默认0.6")
parse.add_argument("-o", "--output", type=str, default="", help="字符串，文件输出目录,默认脚本运行目录")
args = parse.parse_args()

ques_len = args.lenques   #测试数据的生成量不会高于该值
choice_ratid = args.choratid   #多选题的比例

def gene_ques(qtype:bool):
    corr_index = randint(0,3) if qtype else randint(0,1)
    options = ["选项A", "选项B", "选项C", "选项D"] if qtype else ["对", "错"]
    question = f"这题答案是{corr_index}。"
    return {
        "question" : question,
        "options" : options,
        "correct_index":corr_index
    }

choice_len = int(ques_len*choice_ratid)
jubg_len = ques_len - choice_len

ques_list = []
for _ in range(choice_len):
    ques_list.append(gene_ques(True))
for _ in range(jubg_len):
    ques_list.append(gene_ques(False))

questions = {}
qid = 1000
for ques in ques_list:
    questions[qid] = ques
    qid += 1

with open(join(args.output, "question.json"), "tw", encoding="utf8") as qf:
    dump(questions, qf, ensure_ascii=False)