# -*- coding: utf-8 -*-
"""
TensorFlow 1.x 兼容的模型定义模块
包含 LstmWithCRFModel 和 SignalLstmModel
"""
import tensorflow as tf


class LstmWithCRFModel:
    """LSTM + CRF 序列标注模型（用于红球/蓝球序列预测）"""

    def __init__(
        self,
        batch_size: int,
        n_class: int,
        ball_num: int,
        w_size: int,
        embedding_size: int,
        words_size: int,
        hidden_size: int,
        layer_size: int
    ):
        self.batch_size = batch_size
        self.n_class = n_class
        self.ball_num = ball_num
        self.w_size = w_size
        self.embedding_size = embedding_size
        self.words_size = words_size
        self.hidden_size = hidden_size
        self.layer_size = layer_size

        self._build_graph()

    def _build_graph(self):
        """构建计算图"""
        # 输入占位符
        self.inputs = tf.compat.v1.placeholder(
            tf.int32, shape=[None, self.w_size, self.ball_num], name="inputs"
        )
        self.tag_indices = tf.compat.v1.placeholder(
            tf.int32, shape=[None, self.ball_num], name="tag_indices"
        )
        self.sequence_length = tf.compat.v1.placeholder(
            tf.int32, shape=[None], name="sequence_length"
        )
        self.dropout_keep_prob = tf.compat.v1.placeholder(
            tf.float32, name="dropout_keep_prob"
        )

        # Embedding 层
        embedding = tf.Variable(
            tf.random.uniform([self.words_size, self.embedding_size], -0.1, 0.1),
            name="embedding"
        )
        # inputs shape: (batch, w_size, ball_num) -> 展平后做 embedding
        input_shape = tf.shape(self.inputs)
        flat_inputs = tf.reshape(self.inputs, [-1, self.ball_num])
        embedded = tf.nn.embedding_lookup(embedding, flat_inputs)
        embedded = tf.reshape(
            embedded,
            [input_shape[0], self.w_size, self.ball_num * self.embedding_size]
        )

        # LSTM 层
        lstm_cells = []
        for _ in range(self.layer_size):
            cell = tf.compat.v1.nn.rnn_cell.LSTMCell(
                self.hidden_size,
                state_is_tuple=True
            )
            cell = tf.compat.v1.nn.rnn_cell.DropoutWrapper(
                cell, output_keep_prob=self.dropout_keep_prob
            )
            lstm_cells.append(cell)

        multi_cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell(
            lstm_cells, state_is_tuple=True
        )

        outputs, _ = tf.nn.dynamic_rnn(
            multi_cell,
            embedded,
            dtype=tf.float32,
            sequence_length=self.sequence_length
        )

        # 输出层
        logits = tf.compat.v1.layers.dense(
            outputs,
            self.n_class,
            name="output_logits"
        )

        # CRF 层
        log_likelihood, transition_params = tf.contrib.crf.crf_log_likelihood(
            logits, self.tag_indices, self.sequence_length
        )
        self.loss = tf.reduce_mean(-log_likelihood, name="loss")

        # 预测序列
        self.pred_sequence, _ = tf.contrib.crf.crf_decode(
            logits, transition_params, self.sequence_length, name="pred_sequence"
        )

        # 训练操作
        self.train_op = tf.compat.v1.train.AdamOptimizer(
            learning_rate=0.001
        ).minimize(self.loss, name="train_op")


class SignalLstmModel:
    """单信号 LSTM 模型（用于单值预测，如双色球蓝球）"""

    def __init__(
        self,
        batch_size: int,
        n_class: int,
        w_size: int,
        embedding_size: int,
        hidden_size: int,
        outputs_size: int,
        layer_size: int
    ):
        self.batch_size = batch_size
        self.n_class = n_class
        self.w_size = w_size
        self.embedding_size = embedding_size
        self.hidden_size = hidden_size
        self.outputs_size = outputs_size
        self.layer_size = layer_size

        self._build_graph()

    def _build_graph(self):
        """构建计算图"""
        # 输入占位符
        self.inputs = tf.compat.v1.placeholder(
            tf.int32, shape=[None, self.w_size], name="inputs"
        )
        self.tag_indices = tf.compat.v1.placeholder(
            tf.float32, shape=[None, self.n_class], name="tag_indices"
        )
        self.labels = tf.compat.v1.placeholder(
            tf.float32, shape=[None, self.n_class], name="labels"
        )
        self.sequence_length = tf.compat.v1.placeholder(
            tf.int32, shape=[None], name="sequence_length"
        )
        self.dropout_keep_prob = tf.compat.v1.placeholder(
            tf.float32, name="dropout_keep_prob"
        )

        # Embedding 层
        embedding = tf.Variable(
            tf.random.uniform([self.n_class, self.embedding_size], -0.1, 0.1),
            name="embedding"
        )
        embedded = tf.nn.embedding_lookup(embedding, self.inputs)

        # LSTM 层
        lstm_cells = []
        for _ in range(self.layer_size):
            cell = tf.compat.v1.nn.rnn_cell.LSTMCell(
                self.hidden_size,
                state_is_tuple=True
            )
            cell = tf.compat.v1.nn.rnn_cell.DropoutWrapper(
                cell, output_keep_prob=self.dropout_keep_prob
            )
            lstm_cells.append(cell)

        multi_cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell(
            lstm_cells, state_is_tuple=True
        )

        outputs, last_state = tf.nn.dynamic_rnn(
            multi_cell,
            embedded,
            dtype=tf.float32
        )

        # 取最后一个时间步的输出
        last_output = outputs[:, -1, :]

        # 全连接输出层
        logits = tf.compat.v1.layers.dense(
            last_output,
            self.outputs_size,
            name="output_logits"
        )

        # Softmax 输出
        self.pred_label = tf.argmax(
            logits, axis=1, output_type=tf.int32, name="pred_label"
        )

        # 交叉熵损失
        self.loss = tf.reduce_mean(
            tf.nn.softmax_cross_entropy_with_logits(
                labels=self.tag_indices, logits=logits
            ),
            name="loss"
        )

        # 训练操作
        self.train_op = tf.compat.v1.train.AdamOptimizer(
            learning_rate=0.001
        ).minimize(self.loss, name="train_op")
