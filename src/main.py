import sys
import datetime
import getpass
import plotly.graph_objects as go
import plotly.io as pio
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets
from PyQt5.QtWidgets import (
    QLabel, QMessageBox, QTableWidgetItem, QHeaderView, QVBoxLayout,
    QDialog, QLineEdit, QDialogButtonBox, QTableWidget,
    QAbstractItemView, QProgressBar,QTextEdit, QApplication,QGraphicsOpacityEffect, QFrame, QHBoxLayout, QSizePolicy, QWidget, QScrollArea, QPushButton
)
from PyQt5.QtCore import Qt, QEventLoop, QTimer,QPropertyAnimation,QEvent
from PyQt5.QtGui import QIcon, QColor, QPixmap, QFont
from selectSupplier import Ui_windowSelectSupplier
from Interface import Ui_MainWindow
from loginWindow import Ui_LoginWindow
from crud import read, create, update, delete, log_event, buscar_logs
import os, json
from pathlib import Path
from collections import defaultdict



class Functions(QtCore.QObject):
    def __init__(self, ui_login, janela_login,janela_principal, ui_main, janela_select,parent=None):
        super().__init__(parent)
        self.ui_login = ui_login
        self.janela_login = janela_login
        self.janela_principal = janela_principal
        self.ui_main = ui_main 
        self.ui_select = janela_select
        

        
        tab_widget = self.ui_main.tabWidget  

        for i in range(tab_widget.count()):
            tab_widget.setTabIcon(i, QIcon())

        tab_widget = self.ui_main.tabWidget  

        tab_widget.tabBar().hide()




    def mostrar_toast(self, parent, tipo_mensagem, titulo, mensagem):
        """
        1 - Warning
        2 - Error
        3 - Success
        """
        if tipo_mensagem not in (1, 2, 3):
            return

        if not hasattr(self, 'toasts_ativos'):
            self.toasts_ativos = []

        toast = QLabel(None)

        cores = {
            1: "rgba(255, 193, 7, 230)",  
            2: "rgba(244, 67, 54, 230)",   
            3: "rgba(76, 175, 80, 230)"    
        }

        cor_fundo = cores[tipo_mensagem]

        texto_html = f"""
        <div>
            <b>{titulo}</b><br>
            <span>{mensagem}</span>
        </div>
        """
        toast.setText(texto_html)

        toast.setStyleSheet(f"""
            background-color: {cor_fundo};
            color: white;
            padding: 12px 20px;
            font-size: 13px;
            border-radius: 5px;
        """)

        toast.setAttribute(Qt.WA_StyledBackground, True)
        toast.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        toast.setAttribute(Qt.WA_ShowWithoutActivating)
        toast.adjustSize()

        geo = parent.frameGeometry()
        x = geo.x() + geo.width() - toast.width() - 20
        y = geo.y() + 20 + len(self.toasts_ativos) * (toast.height() + 10)

        toast.move(x, y)
        toast.show()

        self.toasts_ativos.append(toast)

        def fade_and_close():
            effect = QGraphicsOpacityEffect(toast)
            toast.setGraphicsEffect(effect)
            toast.effect = effect

            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(1500)
            anim.setStartValue(1)
            anim.setEndValue(0)

            def on_finished():
                toast.close()
                if toast in self.toasts_ativos:
                    self.toasts_ativos.remove(toast)
                    self.reorganizar_toasts(parent)

            anim.finished.connect(on_finished)
            anim.start()
            toast.anim = anim

        QTimer.singleShot(3000, fade_and_close)


    def reorganizar_toasts(self, parent):
        geo = parent.frameGeometry()
        for i, toast in enumerate(self.toasts_ativos):
            x = geo.x() + geo.width() - toast.width() - 20
            y = geo.y() + 20 + i * (toast.height() + 10)
            toast.move(x, y)


    def eventFilter(self, source, event):

        if event.type() == QEvent.Move and source == self.toast_parent:
            if hasattr(self, 'toast') and self.toast.isVisible():

                geo = source.frameGeometry()
                x = geo.x() + geo.width() - self.toast.width() - 20
                y = geo.y() + 20
                self.toast.move(x, y)
        
        return super().eventFilter(source, event)


    def total_score_possivel(self):
        total = (int(ui.quality_packege_criteria.value())*10) + \
                (int(ui.nil_criteria.value())*10) + \
                (int(ui.otif_criteria.value())*10) + \
                (int(ui.quality_pickup_criteria.value())*10)
        
        total_str = f" /{total}"


    def iniciar_splash(self):
        try:
            self.ui_login.btn_login.setEnabled(False)

            wwid_digitado = self.ui_login.wwid_user.text().strip()
            senha_digitada = self.ui_login.password_login.text().strip()

            if not wwid_digitado or not senha_digitada:
                QMessageBox.warning(self.janela_principal, "Login Failed", "Please enter both WWID and password.")
                self.ui_login.btn_login.setEnabled(True)  
                return

            resultado = read("SELECT user_wwid, user_password, user_privilege FROM users_table WHERE user_wwid = ?", (wwid_digitado,))

            if not resultado:
                self.mostrar_toast(janela_login,2,"Login Failed", f"WWID '{wwid_digitado}' not found.")
                self.ui_login.btn_login.setEnabled(True)  
                return

            wwid_banco, senha_banco, privilegio = resultado[0]

            if senha_digitada != senha_banco:
                self.mostrar_toast(janela_login,2,"Login Failed","Incorrect password")
                self.ui_login.btn_login.setEnabled(True)
                return

            self.usuario_logado = {
                "wwid": wwid_banco,
                "privilege": privilegio
            }

            self.ui_login.barra_progresso.setValue(0)
            self.tempo_inicial = QtCore.QElapsedTimer()
            self.tempo_inicial.start()
            self.duracao_total = 1000  

            self.timer = QtCore.QTimer()
            self.timer.setInterval(1)

            def atualizar_barra():
                tempo_passado = self.tempo_inicial.elapsed()
                progresso = min(int((tempo_passado / self.duracao_total) * 100), 100)
                self.ui_login.barra_progresso.setValue(progresso)

                if progresso >= 100:
                    self.timer.stop()
                    if self.ui_login.checkBox_remember_login.isChecked():
                        funcoes.salvar_preferencia_login()
                    self.janela_login.close()
                    self.janela_principal.show()
                    self.verificar_privilegio(wwid_digitado, senha_digitada)
                    self.carregar_graficos()
                

            self.timer.timeout.connect(atualizar_barra)
            self.timer.start()

        except Exception as e:
            self.mostrar_toast(janela_login,2,"Error",f"An unexpected error occurred:\n{str(e)}")
            log_event(f"[Login Error] {str(e)}")
            funcoes.preencher_table_log()
            self.ui_login.btn_login.setEnabled(True)  


        except Exception as e:
            QMessageBox.critical(self.janela_principal, "Error", f"An unexpected error occurred:\n{str(e)}")
            log_event(f"[Login Error] {str(e)}")
            funcoes.preencher_table_log()


    def verificar_privilegio(self, wwid_digitado, senha_digitada):
        try:
            if not hasattr(self, "usuario_logado"):
                QMessageBox.warning(self.janela_principal, "Access Denied", "No user session found.")
                return

            privilegio = self.usuario_logado.get("privilege", "").strip().lower()

            self.ui_main.edit_wwid.setText(wwid_digitado)
            self.ui_main.edit_password.setText(senha_digitada)
            self.ui_main.edit_privilege.setCurrentText(self.usuario_logado["privilege"])

            if privilegio == "admin":
                return

            elif privilegio == "user":
                self.ui_main.btn_score.setVisible(False)
                self.ui_main.groupBox_new_user.setVisible(False)
                self.ui_main.tabWidget.setCurrentIndex(0)
                self.ui_main.widget_edit_privilege.setVisible(False)

                for _ in range(4):  
                    self.ui_main.tabWidget_config.removeTab(1)

            else:
                QMessageBox.warning(self.janela_principal, "Access Denied", f"Unknown privilege level: '{privilegio}'")

        except Exception as e:
            QMessageBox.critical(self.janela_principal, "Error", f"An error occurred while checking privileges:\n{str(e)}")
            log_event(f"[Privilege Check Error] {str(e)}")


    def atualizar_senha(self):
        try:
            wwid = self.ui_main.edit_wwid.text()
            nova_senha = self.ui_main.edit_password.text()
            novo_privilegio = self.ui_main.edit_privilege.currentText()

            if not wwid or not nova_senha or not novo_privilegio:
                funcoes.mostrar_toast(janela_principal, 1, "Invalid Input", "Please fill in WWID, new password, and privilege.")
                return

            resultado = read("SELECT user_privilege FROM users_table WHERE user_wwid = ?", (wwid,))
            if not resultado:
                funcoes.mostrar_toast(janela_principal, 1, "User Not Found", f"No user found with WWID '{wwid}'.")
                return

            privilegio_atual = resultado[0][0]

            if privilegio_atual == "Admin":

                update(
                    "UPDATE users_table SET user_password = ? WHERE user_wwid = ?",
                    (nova_senha, wwid)
                )
            else:

                update(
                    "UPDATE users_table SET user_password = ?, user_privilege = ? WHERE user_wwid = ?",
                    (nova_senha, novo_privilegio, wwid)
                )

            funcoes.mostrar_toast(janela_principal, 3, "Success", "Password changed.")

        except Exception as e:
            funcoes.mostrar_toast(janela_principal, 2, "Error", f"An error occurred while updating data:\n{str(e)}")
            log_event(f"[Update Password/Privilege Error] {str(e)}")
            funcoes.preencher_table_log()


    def adicionar_novo_usuario(self):
        try:
            wwid = self.ui_main.new_wwid.text().strip().upper()
            senha = self.ui_main.new_password.text().strip()
            privilegio = self.ui_main.new_privilege.currentText().strip()

            if not wwid or not senha or not privilegio:
                funcoes.mostrar_toast(janela_principal, 1, "Invalid Input", "Please fill in all fields to add a new user.")
                return

            # Verifica se já existe um usuário com esse WWID (independente de maiúsculas/minúsculas)
            resultado = read("SELECT 1 FROM users_table WHERE UPPER(user_wwid) = ?", (wwid,))
            if resultado:
                funcoes.mostrar_toast(janela_principal, 1, "User Exists", f"User with WWID '{wwid}' already exists.")
                return

            # Insere novo usuário
            create(
                "INSERT INTO users_table (user_wwid, user_password, user_privilege) VALUES (?, ?, ?)",
                (wwid, senha, privilegio)
            )

            funcoes.mostrar_toast(janela_principal, 3, "Success", f"User '{wwid}' added successfully.")

        except Exception as e:
            funcoes.mostrar_toast(janela_principal, 2, "Error", f"An error occurred while adding user:\n{str(e)}")
            log_event(f"[Add User Error] {str(e)}")
            funcoes.preencher_table_log()


    def atualizar_media_12_meses(self):
        id = ui.id_timeline.text().strip()
        if not id:
            ui.average_12month.setText("")
            return

        try:
            registros = read("SELECT * FROM supplier_score_records_table WHERE supplier_id = ?", (id,))
            if not registros:
                ui.average_12month.setText("")
                return

            hoje = QtCore.QDate.currentDate()
            ultimos_12_meses = [(hoje.addMonths(-i).year(), hoje.addMonths(-i).month()) for i in range(11, -1, -1)]

            dados = {}
            for row in registros:
                try:
                    ano = int(row[4])   
                    mes = int(row[3])   
                    score = float(row[9])
                    dados[(ano, mes)] = score
                except:
                    continue

            # Monta a lista de valores dos últimos 12 meses (0 se não houver dado)
            valores = [dados.get((ano, mes), 0) for ano, mes in ultimos_12_meses]

            valores_validos = [v for v in valores if v > 0]
            if not valores_validos:
                ui.average_12month.setText("")
                return

            media_12_meses = sum(valores_validos) / len(valores_validos)
            ui.average_12month.setText(f" {int(media_12_meses)}")

        except Exception as e:
            print(f"Erro ao calcular média dos 12 meses: {e}")
            ui.average_12month.setText("")


    def atualizar_media_anual(self):
        id = ui.id_timeline.text().strip()
        ano_selecionado = ui.year_timeline.currentText().strip()

        if not id:
            ui.average_year.setText("")
            return

        if ano_selecionado == "":
            # Se não selecionou ano, busca todos os anos
            registros = read("SELECT * FROM supplier_score_records_table WHERE supplier_id = ?", (id,))
        else:
            # Filtra pelo ano selecionado
            registros = read(
                "SELECT * FROM supplier_score_records_table WHERE supplier_id = ? AND year = ?",
                (id, int(ano_selecionado))
            )

        if not registros:
            ui.average_year.setText("")
            return

        try:
            scores = []
            # Se ano está vazio, calcula a média de todos os anos
            if ano_selecionado == "":
                for row in registros:
                    score = float(row[9])
                    if score > 0:
                        scores.append(score)
            else:
                # Se ano selecionado, considera só meses até o mês atual
                mes_atual = datetime.datetime.now().month
                for row in registros:
                    mes = int(row[3])
                    score = float(row[9])
                    if 1 <= mes <= mes_atual and score > 0:
                        scores.append(score)

            if not scores:
                ui.average_year.setText("")
                return

            media = sum(scores) / len(scores)
            ui.average_year.setText(f" {int(media)}")

        except Exception:
            ui.average_year.setText("")


    def atualizar_medias_trimestrais(self):
        id = ui.id_timeline.text().strip()
        ano_selecionado = ui.year_timeline.currentText().strip()

        # Limpa os textos e mostra todos widgets inicialmente
        ui.average_q1.setText("")
        ui.average_q2.setText("")
        ui.average_q3.setText("")
        ui.average_q4.setText("")

        ui.widget_q1_timeline.setVisible(True)
        ui.widget_q2_timeline.setVisible(True)
        ui.widget_q3_timeline.setVisible(True)
        ui.widget_q4_timeline.setVisible(True)

        if not id:
            # Se não tem id, oculta todos widgets e sai
            ui.widget_q1_timeline.setVisible(False)
            ui.widget_q2_timeline.setVisible(False)
            ui.widget_q3_timeline.setVisible(False)
            ui.widget_q4_timeline.setVisible(False)
            return

        if ano_selecionado == "":
            registros = read("SELECT * FROM supplier_score_records_table WHERE supplier_id = ?", (id,))
        else:
            registros = read(
                "SELECT * FROM supplier_score_records_table WHERE supplier_id = ? AND year = ?",
                (id, int(ano_selecionado))
            )

        if not registros:
            ui.widget_q1_timeline.setVisible(False)
            ui.widget_q2_timeline.setVisible(False)
            ui.widget_q3_timeline.setVisible(False)
            ui.widget_q4_timeline.setVisible(False)
            return

        trimestres = {
            'q1': [],
            'q2': [],
            'q3': [],
            'q4': []
        }

        for row in registros:
            try:
                mes = int(row[3])
                score = float(row[9])
                if mes in [1, 2, 3]:
                    trimestres['q1'].append(score)
                elif mes in [4, 5, 6]:
                    trimestres['q2'].append(score)
                elif mes in [7, 8, 9]:
                    trimestres['q3'].append(score)
                elif mes in [10, 11, 12]:
                    trimestres['q4'].append(score)
            except:
                continue

        def calcular_media(valores):
            if not valores:
                return None
            return sum(valores) / len(valores)

        medias = {
            'q1': calcular_media(trimestres['q1']),
            'q2': calcular_media(trimestres['q2']),
            'q3': calcular_media(trimestres['q3']),
            'q4': calcular_media(trimestres['q4']),
        }

        # Função para encontrar o trimestre anterior disponível, indo para trás
        def trimestre_anterior_disponivel(atual):
            ordem = ['q1', 'q2', 'q3', 'q4']
            idx = ordem.index(atual)
            for i in range(idx - 1, -1, -1):
                if medias[ordem[i]] is not None:
                    return ordem[i]
            return None

        # Função para montar texto com seta
        def texto_com_seta(atual):
            media_atual = medias[atual]
            if media_atual is None:
                return ""
            anterior = trimestre_anterior_disponivel(atual)
            if anterior is None:
                return f" {int(round(media_atual))}"
            media_anterior = medias[anterior]
            if media_atual > media_anterior:
                seta = '<span style="font-size:18px;"> ▲</span>'
            elif media_atual < media_anterior:
                seta = '<span style="font-size:20px;"> 🔻</span>'
            else:
                seta = '<span style="font-size:18px;"> ▶</span>'
            return f' {int(round(media_atual))}{seta}'
        
        ui.average_q1.setText(texto_com_seta('q1'))
        ui.average_q2.setText(texto_com_seta('q2'))
        ui.average_q3.setText(texto_com_seta('q3'))
        ui.average_q4.setText(texto_com_seta('q4'))

        if medias['q1'] is None:
            ui.widget_q1_timeline.setVisible(False)
        if medias['q2'] is None:
            ui.widget_q2_timeline.setVisible(False)
        if medias['q3'] is None:
            ui.widget_q3_timeline.setVisible(False)
        if medias['q4'] is None:
            ui.widget_q4_timeline.setVisible(False)


    def atualizar_media_geral(self):
        id = ui.id_timeline.text().strip()

        if not id:
            ui.overhall_average.setText("")
            return

        try:
            registros = read("SELECT * FROM supplier_score_records_table WHERE supplier_id = ?", (id,))
            if not registros:
                ui.overhall_average.setText("")
                return

            valores = [float(row[9]) for row in registros if float(row[9]) > 0]
            if not valores:
                ui.overhall_average.setText("")
                return

            media_geral = sum(valores) / len(valores)
            ui.overhall_average.setText(f" {int(media_geral)}")

        except Exception as e:
            ui.overhall_average.setText("")


    def criar_grafico_coluna(self, container_widget):
        id = self.ui_main.id_timeline.text().strip()
        ano_selecionado = ui.year_timeline.currentText().strip()

        if not id:
            return

        if ano_selecionado == "":
            rows = read("SELECT * FROM supplier_score_records_table WHERE supplier_id = ? ORDER BY year, month", (id,))
        else:
            rows = read(
                "SELECT * FROM supplier_score_records_table WHERE supplier_id = ? AND year = ? ORDER BY year, month",
                (id, int(ano_selecionado))
            )

        layout = container_widget.layout()
        if layout is None:
            layout = QtWidgets.QVBoxLayout(container_widget)
            container_widget.setLayout(layout)
            layout.setContentsMargins(0, 0, 0, 0)

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not rows:
            label = QtWidgets.QLabel("No data available for this supplier")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 16px; color: red;")
            layout.addWidget(label)
            return

        rows = sorted(rows, key=lambda x: (int(x[4]), int(x[3])))

        meses_pt = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }

        meses = []
        valores = []
        customdata = []

        for row in rows:
            mes, ano, total, comment = int(row[3]), int(row[4]), float(row[9]), row[10]
            mes_str = f"{meses_pt[mes]}/{str(ano)[2:]}"
            meses.append(mes_str)
            valores.append(total)
            customdata.append([comment if comment else "No comment"])

        def calcular_media_acumulada(lista):
            soma = 0
            return [(soma := soma + v) / (i + 1) for i, v in enumerate(lista)]

        medias_total = calcular_media_acumulada(valores)
        meta = self.ui_main.target_criteria.value()

        cores = [
            'rgba(0, 255, 0, 0.4)' if v >= meta else 'rgba(255, 0, 0, 0.4)'
            for v in valores
        ]

        textos = []
        for i, v in enumerate(valores):
            if i == 0:
                textos.append(f"{v:.1f}")
            else:
                anterior = valores[i - 1]
                if anterior == 0:
                    textos.append(f"{v:.1f} (N/A)")
                else:
                    variacao = ((v - anterior) / anterior) * 100
                    seta = "🔺" if variacao > 0 else "🔻" if variacao < 0 else "➡️"
                    textos.append(f"{v:.1f} ({seta} {abs(variacao):.1f}%)")

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=meses,
            y=valores,
            text=textos,
            textposition='outside',
            marker=dict(
                color=cores,
                line=dict(color='rgba(0,0,0,0.2)', width=1),
            ),
            hovertemplate=
                '<b>Score:</b> %{y}<br>' +
                '<b>Comment:</b> %{customdata[0]}<extra></extra>',
            customdata=customdata,
            showlegend=False
        ))

        fig.add_trace(go.Scatter(
            x=meses,
            y=medias_total,
            name="Avg Score",
            mode='lines+markers',
            line=dict(color='blue', width=1),
            marker=dict(size=6)
        ))

        fig.add_shape(
            type='line',
            x0=0, x1=1,
            y0=meta, y1=meta,
            xref='paper', yref='y',
            line=dict(color='black', width=2, dash='dash')
        )

        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode='lines',
            line=dict(color='black', width=2, dash='dash'),
            name='Target'
        ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="black"),
            margin=dict(l=20, r=20, t=40, b=40),
            yaxis=dict(
                range=[0, 400],
                fixedrange=True,
                showgrid=True,
                showline=True,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

        style_transparente = """
        <style>
            body {
                background-color: rgba(0,0,0,0) !important;
                margin: 0;
            }

            .barlayer path,
            g.barlayer .point path {
                cursor: pointer !important;
            }
        </style>
        """

        script_no_modebar = "<script>window.PlotlyConfig = {displayModeBar: false};</script>"
        html = style_transparente + script_no_modebar + html

        web_view = QtWebEngineWidgets.QWebEngineView()
        web_view.setStyleSheet("background: transparent")
        web_view.setHtml(html, QtCore.QUrl("about:blank"))
        layout.addWidget(web_view)


    def preencher_tabela_resultados(self):
        id_fornecedor = ui.id_timeline.text().strip()
        ano_selecionado = ui.year_timeline.currentText().strip()

        if not id_fornecedor:
            ui.tableDetails.clearContents()
            ui.tableDetails.setRowCount(0)
            return

        if ano_selecionado == "":
            query = """
                SELECT * 
                FROM supplier_score_records_table 
                WHERE supplier_id = ?
            """
            params = (id_fornecedor,)
        else:
            query = """
                SELECT * 
                FROM supplier_score_records_table 
                WHERE supplier_id = ? AND year = ?
            """
            params = (id_fornecedor, int(ano_selecionado))

        rows = read(query, params)
        if not rows:
            ui.tableDetails.clearContents()
            ui.tableDetails.setRowCount(0)
            return

        # Ordenar pela data (ano e mês), do mais novo para o mais antigo
        rows_ordenados = sorted(
            rows,
            key=lambda r: int(f"{int(r[4]):04}{int(r[3]):02}"),  # YYYYMM
            reverse=True
        )

        tabela = ui.tableDetails
        tabela.setSortingEnabled(False)
        tabela.clearContents()
        tabela.setRowCount(len(rows_ordenados))
        tabela.setColumnCount(9)
        tabela.setHorizontalHeaderLabels([
            "ID", "Date", "Quality Package", "Quality Pick Up", "NIL", "OTIF", "Total Score", "Editor", "Comments"
        ])

        for i, row in enumerate(rows_ordenados):
            row_id = row[0]
            mes = row[3]
            ano = row[4]
            q_package = row[5]
            q_pickup = row[6]
            nil = row[7]
            otif = row[8]
            total = row[9]
            comment = row[10]
            editor = row[14]  # changed_by

            data_formatada = f"{int(mes):02}/{ano}"
            valores = [row_id, data_formatada, q_package, q_pickup, nil, otif, total, editor, comment]

            for j, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignCenter)
                tabela.setItem(i, j, item)

        header = tabela.horizontalHeader()
        header.setSectionResizeMode(8, QHeaderView.Stretch)

        tabela.resizeColumnsToContents()
        tabela.resizeRowsToContents()
        tabela.setSortingEnabled(True)


    def carregar_graficos(self):
        self.criar_grafico_coluna(self.ui_main.lineChart)
        self.atualizar_media_12_meses()
        self.atualizar_media_anual()
        self.atualizar_medias_trimestrais()
        self.atualizar_media_geral()
        self.preencher_tabela_resultados()
        self.total_score_possivel()
        

    def mudar_pagina(indice):
        ui.tabWidget.setCurrentIndex(indice)
        
        if ui.tabWidget.currentIndex() == 3:
            funcoes.verificar_riscos()
            funcoes.fechar_grafico_risco()

        elif ui.tabWidget.currentIndex() == 2:
            funcoes.preencher_tabela_resultados()
            funcoes.carregar_graficos()

        buttons = [
            ui.btn_home,
            ui.btn_score,
            ui.btn_timeline,
            ui.btn_risks,
            ui.btn_configs
        ]

        max_border = 5  
        duration = 100  
        steps = 30      
        delay = duration / steps

        for i, btn in enumerate(buttons):
            if i != indice:
                style = f"""
                    QPushButton#{btn.objectName()} {{
                        background-color: transparent;
                        border: none;
                        border-left: none;
                        border-radius: 0px;
                        text-align: left;
                        padding: 10px;
                        color: rgb(150,150,150);  /* Texto cinza */
                        font-weight: normal;
                        outline: none;
                    }}
                    QPushButton#{btn.objectName()}:hover {{
                        background-color: transparent;
                        color: rgb(98, 114, 164);  /* Azul no hover */
                        font-weight: bold;
                        border-left: 3px solid rgba(98, 114, 164, 255);
                        outline: none;
                    }}
                """
                btn.setStyleSheet(style)

       
        selected_btn = buttons[indice]
        style = f"""
            QPushButton#{selected_btn.objectName()} {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
                text-align: left;
                padding: 10px;
                color: rgb(98, 114, 164);  /* Texto azul */
                border-left: 3px solid rgba(98, 114, 164, 255);
                font-weight: bold;
                outline: none;
            }}
            QPushButton#{selected_btn.objectName()}:hover {{
                background-color: transparent;
                color: rgb(98, 114, 164);
                font-weight: bold;
                border-left: 3px solid rgba(98, 114, 164, 255);
                outline: none;
            }}
        """
        selected_btn.setStyleSheet(style)
        loop = QEventLoop()
        QTimer.singleShot(int(delay), loop.quit)
        loop.exec_()


    def total_score_calculate():
        quality_package = ui.quality_package_input.value() * ui.quality_packege_criteria.value()
        quality_pick = ui.quality_pickup_input.value() * ui.quality_pickup_criteria.value()
        nil = ui.nil_input.value() * ui.nil_criteria.value()
        otif = ui.otif_input.value() * ui.otif_criteria.value()
        total_score = quality_package + quality_pick + otif + nil

        ui.total_score.setValue(total_score)


    def salvar_score(self):
        try:
            # Coleta os dados da interface
            id_fornecedor = ui.id_query.text().strip()
            fornecedor = ui.vendor_select.text().strip()
            mes = ui.month.currentText().strip()
            ano = ui.year.currentText().strip()
            pacote = ui.quality_package_input.value()
            retirada = ui.quality_pickup_input.value()
            nil = ui.nil_input.value()
            otif = ui.otif_input.value()
            total = ui.total_score.text().strip()
            comment = ui.comments.toPlainText()
            user = getpass.getuser()
            register_date = datetime.datetime.now()

            
            if not id_fornecedor or fornecedor == "" or mes == "" or ano == "": 
                funcoes.mostrar_toast(janela_principal,1,"Warning", "Supplier ID, name, month, and year are required to save the score.")
                log_event("Error while saving score: Missing required fields."); funcoes.preencher_table_log()
                funcoes.preencher_table_log()
                return


            existe = read(
                "SELECT 1 FROM supplier_score_records_table WHERE supplier_id = ? AND month = ? AND year = ?",
                (id_fornecedor, mes, ano)
            )

            if existe:
                resposta = QMessageBox.question(
                    janela_principal,
                    "Duplicate Entry",
                    "This supplier already has a score registered for this month and year.\nDo you want to overwrite it?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if resposta == QMessageBox.No:
                    return

                
                query_update = """
                    UPDATE supplier_score_records_table
                    SET quality_package = ?, quality_pickup = ?, nil = ?, otif = ?,
                        total_score = ?, comment = ?, changed_by = ?, register_date = ?
                    WHERE supplier_id = ? AND month = ? AND year = ?
                """
                params_update = (
                    pacote, retirada, nil, otif,
                    total, comment, user, register_date,
                    id_fornecedor, mes, ano
                )
                update(query_update, params_update)
                funcoes.mostrar_toast(janela_principal,3,"Success", "Score updated successfully.")
                
            else:
                
                query_insert = """
                    INSERT INTO supplier_score_records_table (
                        supplier_id, supplier_name, month, year,
                        quality_package, quality_pickup, nil, otif,
                        total_score, comment, register_date, changed_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params_insert = (
                    id_fornecedor, fornecedor, mes, ano,
                    pacote, retirada, nil, otif,
                    total, comment, register_date, user
                )
                create(query_insert, params_insert)
                funcoes.mostrar_toast(janela_principal,3,"Success", "Score saved successfully.")
                

            ui.id_query.setText("")
            ui.vendor_select.setText("")
            ui.month.setCurrentIndex(0)
            ui.year.setCurrentIndex(0)
            ui.quality_package_input.setValue(0)
            ui.quality_pickup_input.setValue(0)
            ui.nil_input.setValue(0)
            ui.otif_input.setValue(0)
            ui.total_score.setValue(0)
            ui.comments.clear()
            ui.bu_query.setText("")
            ui.status_query.setText("")
            ui.number_query.setText("")
            funcoes.verificar_riscos()

        except Exception as e:
            # Em caso de erro inesperado
            funcoes.mostrar_toast(janela_principal, 2, "Error", "An error occurred while saving")
 
            log_event(f"Error while saving score: {str(e)}"); funcoes.preencher_table_log() 
           

    def gerar_lista_nota_cheia(self):
        try:
            mes = ui.month_group_input.currentText().strip()
            ano = ui.year_group_input.currentText().strip()

            if not mes or not ano:
                QMessageBox.warning(janela_principal, "Warning", "Month and year must be selected to generate scores.")
                log_event("Error while generating scores: Month and/or Year not selected."); funcoes.preencher_table_log()
                return

            # Confirmação inicial
            confirm = QMessageBox.question(
                janela_principal,
                "Confirmation",
                "Are you sure you want to generate full score records for the selected month and year?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm != QMessageBox.Yes:
                return

            criterios_raw = read("SELECT criteria_category, value FROM criteria_table")

            criterio_map = {}
            for row in criterios_raw:
                nome = str(row[0]).strip().lower()
                valor = int(row[1])
                if "package" in nome:
                    criterio_map["package"] = valor
                elif "pick" in nome:
                    criterio_map["pickup"] = valor
                elif "nil" in nome:
                    criterio_map["nil"] = valor
                elif "otif" in nome:
                    criterio_map["otif"] = valor

            if not all(k in criterio_map for k in ["package", "pickup", "nil", "otif"]):
                funcoes.mostrar_toast(janela_principal,2,"Error", "One or more scoring criteria are missing in criteria_table.")
                log_event("Error while generating scores: Missing criteria."); funcoes.preencher_table_log()
                return

            fornecedores = read("SELECT supplier_id, vendor_name, supplier_status FROM supplier_database_table")

            if not fornecedores:
                funcoes.mostrar_toast(janela_principal,1,"Info", "No suppliers found in database.")
                return

            user = getpass.getuser()
            register_date = datetime.datetime.now()

            progresso_dialog = QDialog(janela_principal)
            progresso_dialog.setWindowTitle("Generating Scores")
            progresso_dialog.resize(400, 300)

            layout = QVBoxLayout(progresso_dialog)

            barra_progresso = QProgressBar()
            barra_progresso.setRange(0, len(fornecedores))
            layout.addWidget(barra_progresso)

            campo_log = QTextEdit()
            campo_log.setReadOnly(True)
            layout.addWidget(campo_log)

            progresso_dialog.show()
            QApplication.processEvents()

            adicionados = 0
            ignorados_inativos = 0
            ignorados_existentes = 0

            for i, fornecedor in enumerate(fornecedores):
                barra_progresso.setValue(i)
                QApplication.processEvents()

                supplier_id = fornecedor[0]
                supplier_name = fornecedor[1]
                status = fornecedor[2].strip().lower()

                if status != "active":
                    campo_log.append(f"IGNORED (inactive) - {supplier_name}")
                    ignorados_inativos += 1
                    continue

                existe = read(
                    "SELECT 1 FROM supplier_score_records_table WHERE supplier_id = ? AND month = ? AND year = ?",
                    (supplier_id, mes, ano)
                )
                if existe:
                    campo_log.append(f"IGNORED (already exists) - {supplier_name}")
                    ignorados_existentes += 1
                    continue

                nota_fixa = 10
                total = (
                    nota_fixa * criterio_map["otif"] +
                    nota_fixa * criterio_map["nil"] +
                    nota_fixa * criterio_map["package"] +
                    nota_fixa * criterio_map["pickup"]
                )

                query_insert = """
                    INSERT INTO supplier_score_records_table (
                        supplier_id, supplier_name, month, year,
                        quality_package, quality_pickup, nil, otif,
                        total_score, comment, register_date, changed_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    supplier_id, supplier_name, mes, ano,
                    nota_fixa, nota_fixa, nota_fixa, nota_fixa,
                    total, "Maximum score auto-generated.", register_date, user
                )
                create(query_insert, params)

                campo_log.append(f"ADDED - {supplier_name}")
                adicionados += 1

            barra_progresso.setValue(len(fornecedores))
            QApplication.processEvents()

            progresso_dialog.close()
            del progresso_dialog

            funcoes.preencher_tabela_grupo()

            QMessageBox.information(
                janela_principal,
                "Score Generation Complete",
                f"Score generation completed successfully.\n\n"
                f"• added: {adicionados}\n"
                f"• ignored (inactive): {ignorados_inativos}\n"
                f"• ignored (already exists): {ignorados_existentes}"
            )

        except Exception as e:
            funcoes.mostrar_toast(janela_principal,2,"Error", f"An error occurred while generating scores:\n{str(e)}")
            log_event(f"Error while generating scores: {str(e)}"); funcoes.preencher_table_log()


    def preencher_tabela_grupo(self):
        try:
            mes = ui.month_group_input.currentText().strip()
            ano = ui.year_group_input.currentText().strip()

            if not mes or not ano:
                funcoes.mostrar_toast(janela_principal,1, "Warning", "Month and year must be selected to load data.")
                return

            query = """
                SELECT id, supplier_id, supplier_name, otif, nil, quality_pickup, quality_package, total_score
                FROM supplier_score_records_table
                WHERE month = ? AND year = ?
                ORDER BY supplier_name
            """
            resultados = read(query, (mes, ano))

            ui.table_group_input.clearContents()
            ui.table_group_input.setRowCount(0)

            if not resultados:
                QMessageBox.information(janela_principal, "Info", "No score records found for the selected month and year.")
                return

            ui.table_group_input.setRowCount(len(resultados))
            ui.table_group_input.setColumnCount(8)

            headers = ["ID", "Supplier ID", "Vendor Name", "OTIF", "NIL", "Pickup", "Package", "Total"]
            ui.table_group_input.setHorizontalHeaderLabels(headers)

            target = float(ui.target_criteria.value())

            # Primeiro preenche todos os itens sem formatação
            for row_idx, row_data in enumerate(resultados):
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    
                    if col_idx != 2:  # Alinha ao centro exceto Vendor Name
                        item.setTextAlignment(Qt.AlignCenter)
                    
                    ui.table_group_input.setItem(row_idx, col_idx, item)

            # AGORA aplica as cores na coluna "Total" (coluna 7)
            for row_idx in range(ui.table_group_input.rowCount()):
                item = ui.table_group_input.item(row_idx, 7)  # Coluna Total
                if item is not None:
                    try:
                        valor_total = float(item.text())
                        if valor_total >= target:
                            item.setBackground(QColor(180, 255, 180))  # Verde
                        else:
                            item.setBackground(QColor(255, 180, 180))  # Vermelho
                    except ValueError:
                        pass  # Ignora valores não numéricos

            # Ajuste de largura das colunas
            largura_total = ui.table_group_input.viewport().width()
            colunas_fixas = [0, 1, 3, 4, 5, 6, 7]
            largura_fixa = 80
            total_fixo = largura_fixa * len(colunas_fixas)
            largura_vendor = max(largura_total - total_fixo, 100)
            
            for col in colunas_fixas:
                ui.table_group_input.setColumnWidth(col, largura_fixa)
            ui.table_group_input.setColumnWidth(2, largura_vendor)

        except Exception as e:
            funcoes.mostrar_toast(janela_principal,2,"Error", f"An error occurred while loading table data:\n{str(e)}")
            log_event(f"Error while loading table data: {str(e)}"); funcoes.preencher_table_log()


    def apagar_todos_campos_register(self):
        ui.vendor_update.setText("")
        ui.category_update.setCurrentText("")
        ui.bu_update.setCurrentText("")
        ui.supplier_update.setText("")
        ui.sqie_update.setCurrentText("")
        ui.sourcing_update.setCurrentText("")
        ui.continuity_update.setCurrentText("")
        ui.ssid_update.setText("")           
        ui.country_update.setText("")        
        ui.region_update.setText("")       
        ui.document_update.setText("")
        ui.planner_update.setCurrentText("")
        ui.id_update.setText("")
        ui.supplier_status_update.setCurrentText("")
        ui.email_update.setPlainText("")
        ui.supplier_number_update.setText("")
    

    def apagar_todos_campos_query(self):
        ui.vendor_select.setText("")
        ui.bu_query.setText("")
        ui.id_query.setText("")
        ui.number_query.setText("")
        ui.status_query.setText("")
        ui.comments.setPlainText("")
        ui.otif_input.setValue(0)
        ui.nil_input.setValue(0)
        ui.quality_package_input.setValue(0)
        ui.quality_pickup_input.setValue(0)
        ui.month.setCurrentText("")
        ui.year.setCurrentText("")


    def adicionar_sqie(self):
        name = ui.new_sqe.text().strip()
        alias = ui.new_alias_sqie.text().strip().upper()
        email = ui.new_sqe_email.text().strip()
        registered_by = getpass.getuser()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not name or not alias or not email:
            funcoes.mostrar_toast(janela_principal, 1, "Warning", "All fields are required: name, alias, and email.")
            return  

        try:
            resultado = read("SELECT sqie_id FROM sqie_table WHERE alias = ?", (alias,))
            if resultado:
                resposta = QMessageBox.question(
                    None,
                    "Alias Exists",
                    f"The alias '{alias}' already exists. Do you want to edit the existing entry?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if resposta == QMessageBox.Yes:
                    sqie_id = resultado[0][0]
                    update(
                        "UPDATE sqie_table SET name = ?, email = ?, change_date_change_by = ? WHERE sqie_id = ?",
                        (name, email, f"{now} | {registered_by}", sqie_id)
                    )
                    log_event(f"[UPDATE] Edited SQIE alias '{alias}' by {registered_by}")
                    self.carregar_todos_sqie()
                    funcoes.mostrar_toast(janela_principal, 3, "Success", f"SQIE '{alias}' updated successfully.")
                    ui.new_sqie.clear()
                    ui.new_alias_sqie.clear()
                    ui.new_sqie_email.clear()
                    self.preencher_table_log()
                return

            create(
                "INSERT INTO sqie_table (name, alias, email, register_date, registered_by) VALUES (?, ?, ?, ?, ?)",
                (name, alias, email, now, registered_by),
                log_description=f"Added new SQIE '{name}' with alias '{alias}' by {registered_by}"
            )

            self.carregar_todos_sqie()
            funcoes.mostrar_toast(janela_principal, 3, "Success", f"SQIE '{alias}' added successfully.")
            ui.new_sqie.clear()
            ui.new_alias_sqie.clear()
            ui.new_sqie_email.clear()
            self.preencher_table_log()

        except Exception as e:
            log_event(f"[ERROR] Failed to add/edit SQIE: {str(e)}")
            funcoes.mostrar_toast(janela_principal, 2, "Error", f"An error occurred while adding/editing SQIE: {e}")
            self.preencher_table_log()


    def adicionar_continuity(self):
        name = ui.new_continuity.text().strip()
        alias = ui.new_alias_continuity.text().strip().upper()
        email = ui.new_continuity_email.text().strip()
        registered_by = getpass.getuser()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not name or not alias or not email:
            funcoes.mostrar_toast(janela_principal, 1, "Warning", "All fields are required: name, alias, and email.")
            return  

        try:
            resultado = read("SELECT continuity_id FROM continuity_table WHERE alias = ?", (alias,))
            if resultado:
                resposta = QMessageBox.question(
                    None,
                    "Alias Exists",
                    f"The alias '{alias}' already exists. Do you want to edit the existing entry?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if resposta == QMessageBox.Yes:
                    continuity_id = resultado[0][0]
                    update(
                        "UPDATE continuity_table SET name = ?, email = ?, change_date_change_by = ? WHERE continuity_id = ?",
                        (name, email, f"{now} | {registered_by}", continuity_id)
                    )
                    log_event(f"[UPDATE] Edited continuity alias '{alias}' by {registered_by}")
                    self.carregar_todos_continuity()
                    funcoes.mostrar_toast(janela_principal, 3, "Success", f"Continuity '{alias}' updated successfully.")
                    ui.new_continuity.clear()
                    ui.new_alias_continuity.clear()
                    ui.new_continuity_email.clear()
                    self.preencher_table_log()
                return

            create(
                "INSERT INTO continuity_table (name, alias, email, register_date, registered_by) VALUES (?, ?, ?, ?, ?)",
                (name, alias, email, now, registered_by),
                log_description=f"Added new continuity '{name}' with alias '{alias}' by {registered_by}"
            )

            self.carregar_todos_continuity()
            funcoes.mostrar_toast(janela_principal, 3, "Success", f"Continuity '{alias}' added successfully.")
            ui.new_continuity.clear()
            ui.new_alias_continuity.clear()
            ui.new_continuity_email.clear()
            self.preencher_table_log()

        except Exception as e:
            log_event(f"[ERROR] Failed to add/edit continuity: {str(e)}")
            funcoes.mostrar_toast(janela_principal, 2, "Error", f"An error occurred while adding/editing continuity: {e}")
            self.preencher_table_log()


    def adicionar_planner(self):
        name = ui.new_planner.text().strip()
        alias = ui.new_alias_planner.text().strip().upper()
        email = ui.new_planner_email.text().strip()
        registered_by = getpass.getuser()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not name or not alias or not email:
            funcoes.mostrar_toast(janela_principal, 1, "Warning", "All fields are required: name, alias, and email.")
            return

        try:
            resultado = read("SELECT planner_id FROM planner_table WHERE alias = ?", (alias,))
            if resultado:
                resposta = QMessageBox.question(
                    None,
                    "Alias Exists",
                    f"The alias '{alias}' already exists. Do you want to edit the existing entry?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if resposta == QMessageBox.Yes:
                    planner_id = resultado[0][0]
                    update(
                        "UPDATE planner_table SET name = ?, email = ?, change_date_change_by = ? WHERE planner_id = ?",
                        (name, email, f"{now} | {registered_by}", planner_id)
                    )
                    log_event(f"[UPDATE] Edited planner alias '{alias}' by {registered_by}")
                    self.carregar_todos_planner()
                    funcoes.mostrar_toast(janela_principal, 3, "Success", f"Planner '{alias}' updated successfully.")
                    ui.new_planner.clear()
                    ui.new_alias_planner.clear()
                    ui.new_planner_email.clear()
                    self.preencher_table_log()
                return

            create(
                "INSERT INTO planner_table (name, alias, email, register_date, registered_by) VALUES (?, ?, ?, ?, ?)",
                (name, alias, email, now, registered_by),
                log_description=f"Added new planner '{name}' with alias '{alias}' by {registered_by}"
            )

            self.carregar_todos_planner()
            funcoes.mostrar_toast(janela_principal, 3, "Success", f"Planner '{alias}' added successfully.")
            ui.new_planner.clear()
            ui.new_alias_planner.clear()
            ui.new_planner_email.clear()
            self.preencher_table_log()

        except Exception as e:
            log_event(f"[ERROR] Failed to add/edit planner: {str(e)}")
            funcoes.mostrar_toast(janela_principal, 2, "Error", f"An error occurred while adding/editing planner: {e}")
            self.preencher_table_log()


    def adicionar_sourcing(self):
        name = ui.new_sourcing.text().strip()
        alias = ui.new_alias_sourcing.text().strip().upper()
        email = ui.new_sourcing_email.text().strip()
        registered_by = getpass.getuser()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not name or not alias or not email:
            funcoes.mostrar_toast(janela_principal, 1, "Warning", "All fields are required: name, alias, and email.")
            return

        try:
            resultado = read("SELECT sourcing_id FROM sourcing_table WHERE alias = ?", (alias,))
            if resultado:
                resposta = QMessageBox.question(
                    None,
                    "Alias Exists",
                    f"The alias '{alias}' already exists. Do you want to edit the existing entry?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if resposta == QMessageBox.Yes:
                    sourcing_id = resultado[0][0]
                    update(
                        "UPDATE sourcing_table SET name = ?, email = ?, change_date_change_by = ? WHERE sourcing_id = ?",
                        (name, email, f"{now} | {registered_by}", sourcing_id)
                    )
                    log_event(f"[UPDATE] Edited sourcing alias '{alias}' by {registered_by}")
                    self.carregar_todos_sourcing()
                    funcoes.mostrar_toast(janela_principal, 3, "Success", f"Sourcing '{alias}' updated successfully.")
                    ui.new_sourcing.clear()
                    ui.new_alias_sourcing.clear()
                    ui.new_sourcing_email.clear()
                    self.preencher_table_log()
                return

            create(
                "INSERT INTO sourcing_table (name, alias, email, register_date, registered_by) VALUES (?, ?, ?, ?, ?)",
                (name, alias, email, now, registered_by),
                log_description=f"Added new sourcing '{name}' with alias '{alias}' by {registered_by}"
            )

            self.carregar_todos_sourcing()
            funcoes.mostrar_toast(janela_principal, 3, "Success", f"Sourcing '{alias}' added successfully.")
            ui.new_sourcing.clear()
            ui.new_alias_sourcing.clear()
            ui.new_sourcing_email.clear()
            self.preencher_table_log()

        except Exception as e:
            log_event(f"[ERROR] Failed to add/edit sourcing: {str(e)}")
            funcoes.mostrar_toast(janela_principal, 2, "Error", f"An error occurred while adding/editing sourcing: {e}")
            self.preencher_table_log()


    def adicionar_bu(self):
        bu = ui.new_bu.text().strip()
        registered_by = getpass.getuser()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not bu:
            return  

        try:
            resultado = read("SELECT business_id FROM business_unit_table WHERE bu = ?", (bu,))
            if resultado:
                funcoes.mostrar_toast(janela_principal, 1, "Already Exists", f"The Business Unit '{bu}' already exists.")
                return

            create(
                "INSERT INTO business_unit_table (bu, register_date, registered_by) VALUES (?, ?, ?)",
                (bu, now, registered_by),
                log_description=f"Added new Business Unit '{bu}' by {registered_by}"
            )

            self.carregar_todos_bus()
            funcoes.mostrar_toast(janela_principal,3,"Success", f"Business Unit '{bu}' added successfully.")
            ui.new_bu.clear()
            self.preencher_table_log()

        except Exception as e:
            log_event(f"[ERROR] Failed to add Business Unit: {str(e)}")
            self.preencher_table_log()


    def adicionar_category(self):
        category = ui.new_category_2.text().strip()
        registered_by = getpass.getuser()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not category:
            funcoes.mostrar_toast(janela_principal, 1, "Warning", "Category name cannot be empty.")
            return

        try:
            resultado = read("SELECT categories_id FROM categories_table WHERE category = ?", (category,))
            if resultado:
                funcoes.mostrar_toast(janela_principal, 1, "Warning", f"The category '{category}' already exists.")
                return

            create(
                "INSERT INTO categories_table (category, register_date, registered_by) VALUES (?, ?, ?)",
                (category, now, registered_by),
                log_description=f"Added new category '{category}' by {registered_by}"
            )

            self.carregar_todos_categories()
            funcoes.mostrar_toast(janela_principal, 3, "Success", f"Category '{category}' added successfully.")
            ui.new_category_2.clear()
            self.preencher_table_log()

        except Exception as e:
            log_event(f"[ERROR] Failed to add category: {str(e)}")
            funcoes.mostrar_toast(janela_principal, 2, "Error", f"An error occurred while adding category: {e}")
            self.preencher_table_log()


    def carregar_criterios_dos_campos(self):
        campos = {
            "Quality-Supplier Package": ui.quality_packege_criteria,
            "Quality of Pick Up": ui.quality_pickup_criteria,
            "NIL": ui.nil_criteria,
            "OTIF": ui.otif_criteria,
            "Target": ui.target_criteria
        }
        try:
            resultados = read("SELECT * FROM criteria_table")
            for criterio_nome, spinbox in campos.items():
                valor_str = None
                for linha in resultados:
                    if linha[1] == criterio_nome:  
                        valor_str = linha[2]        
                        break
                if valor_str is not None:
                    try:
                        valor = int(float(valor_str))
                        spinbox.setValue(valor)
                    except Exception as conv_erro:
                        log_event(f"[Conversion Error] Failed to convert value for '{criterio_nome}': '{valor_str}' | Error → {conv_erro}"); funcoes.preencher_table_log()
                else:
                    log_event(f"[Warning] No value found for '{criterio_nome}' in criteria_table"); funcoes.preencher_table_log()
        except Exception as e:
            log_event(f"[Critical Error] Failed to load criteria: {e}"); funcoes.preencher_table_log()


    def carregar_fornecedores_do_banco(self):
        try:
            resultados = read("SELECT * FROM supplier_database_table")

            fornecedores = [str(linha[0]) for linha in sorted(resultados, key=lambda x: x[0])]
            fornecedores.insert(0, "")

            return fornecedores
        except Exception as erro:
            print(f"[ERRO - carregar_fornecedores_do_banco] {erro}")
            return [""]


    def atualizar_criterios_no_banco(self):
        try:
            campos = {
                "Quality-Supplier Package": ui.quality_packege_criteria.value(),
                "Quality of Pick Up": ui.quality_pickup_criteria.value(),
                "NIL": ui.nil_criteria.value(),
                "OTIF": ui.otif_criteria.value(),
                "Target": ui.target_criteria.value()
            }

            for categoria, valor in campos.items():
                query = "UPDATE criteria_table SET value = ? WHERE criteria_category = ?"
                params = (valor, categoria)
                update(query, params)

            # Bloqueia os campos após salvar
            ui.quality_packege_criteria.setEnabled(False)
            ui.quality_pickup_criteria.setEnabled(False)
            ui.nil_criteria.setEnabled(False)
            ui.otif_criteria.setEnabled(False)
            ui.target_criteria.setEnabled(False)
            ui.btn_unlock_criteria_edit.setText("🔒")

            funcoes.mostrar_toast(janela_principal,3,"Success", "Criteria updated")
        except Exception as e:
            log_event(f"[Error] Failed to update criteria: {e}"); funcoes.preencher_table_log()


    def carregar_todos_categories(self):
        try:
            resultados = read("SELECT * FROM categories_table")
            categorias = sorted(set(row[1] for row in resultados))  

            ui.new_category.clear()
            ui.category_update.clear()

            ui.new_category.addItem("")        
            ui.category_update.addItem("")    

            for categoria in categorias:
                ui.new_category.addItem(categoria)
                ui.category_update.addItem(categoria)

        except Exception as e:
            print(f"Erro ao carregar categories: {e}")


    def carregar_todos_bus(self):
        try:
            resultados = read("SELECT * FROM business_unit_table")
            bus = sorted(set(row[1] for row in resultados))

            ui.bu_update.clear()
            ui.bu_update.addItem("")
            ui.bu_register_new.clear()
            ui.bu_register_new.addItem("")

            for b in bus:
                ui.bu_update.addItem(b)
                ui.bu_register_new.addItem(b)

        except Exception as e:
            print(f"Erro ao carregar business units: {e}")


    def carregar_todos_continuity(self):
        try:
            resultados = read("SELECT * FROM continuity_table")
            nomes = sorted(row[1] for row in resultados) 

            self.ui_main.continuity_update.clear()
            self.ui_main.continuity_update.addItem("")
            self.ui_main.continuity_update.addItems(nomes)
            self.ui_main.continuity_register_new.clear()
            self.ui_main.continuity_register_new.addItem("")
            self.ui_main.continuity_register_new.addItems(nomes)

        except Exception as e:
            print(f"Erro ao carregar continuity: {e}")


    def carregar_todos_sourcing(self):
        try:
            resultados = read("SELECT * FROM sourcing_table")
            nomes = sorted(row[1] for row in resultados)

            self.ui_main.sourcing_update.clear()
            self.ui_main.sourcing_update.addItem("")
            self.ui_main.sourcing_update.addItems(nomes)
            self.ui_main.sourcing_register_new.clear()
            self.ui_main.sourcing_register_new.addItem("")
            self.ui_main.sourcing_register_new.addItems(nomes)

        except Exception as e:
            print(f"Erro ao carregar sourcing: {e}")


    def carregar_todos_sqie(self):
        '''----------Corrigido-----------'''
        try:
            resultados = read("SELECT * FROM sqie_table")
            nomes = sorted(row[1] for row in resultados)

            self.ui_main.sqie_update.clear()
            self.ui_main.sqie_update.addItem("")
            self.ui_main.sqie_update.addItems(nomes)
            self.ui_main.sqie_register_new.clear()
            self.ui_main.sqie_register_new.addItem("")
            self.ui_main.sqie_register_new.addItems(nomes)

        except Exception as e:
            pass


    def carregar_todos_planner(self):
        '''----------Corrigido-----------'''
        try:
            resultados = read("SELECT * FROM planner_table")
            nomes = sorted(row[1] for row in resultados)

            self.ui_main.planner_update.clear()
            self.ui_main.planner_update.addItem("")
            self.ui_main.planner_update.addItems(nomes)
            self.ui_main.planner_register_new.clear()
            self.ui_main.planner_register_new.addItem("")
            self.ui_main.planner_register_new.addItems(nomes)

        except Exception as e:
            pass


    def salvar_novo_supplier(self):
        vendor = ui.vendor_register_new.text().strip()
        supplier = ui.supplier_register.text().strip()
        category = ui.new_category.currentText().strip()
        status = ui.supplier_status_new.currentText().strip()
        bu = ui.bu_register_new.currentText().strip()
        supplier_number = ui.new_supplier_number.text().strip()
        ssid = ui.ssid_register_new.text().strip()
        country = ui.country_register_new.text().strip()
        region = ui.region_register_new.text().strip()
        document = ui.document_register_new.text().strip()
        sqie = ui.sqie_register_new.currentText().strip()
        continuity = ui.continuity_register_new.currentText().strip()
        sourcing = ui.sourcing_register_new.currentText().strip()
        planner = ui.planner_register_new.currentText().strip()
        email = ui.email_register_new.toPlainText().strip()

        if not vendor or not supplier or not category or not status:
            funcoes.mostrar_toast(janela_principal, 1, "Warning", "Please fill in all mandatory fields: Vendor, Supplier, Category, and Status.")
            return

        query = """
            INSERT INTO supplier_database_table (
                vendor_name, supplier_category, bu, supplier_name,
                supplier_email, supplier_number, supplier_status, planner,
                continuity, sourcing, sqie, ssid,
                country, region, document
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            vendor, category, bu, supplier,
            email, supplier_number, status, planner,
            continuity, sourcing, sqie, ssid,
            country, region, document
        )

        try:
            create(query, params, log_description=f"New supplier saved: {supplier}")

            # Clear fields on success
            ui.vendor_register_new.clear()
            ui.supplier_register.clear()
            ui.new_category.setCurrentIndex(0)
            ui.supplier_status_new.setCurrentIndex(0)
            ui.bu_register_new.setCurrentIndex(0)
            ui.new_supplier_number.clear()
            ui.ssid_register_new.clear()
            ui.country_register_new.clear()
            ui.region_register_new.clear()
            ui.document_register_new.clear()
            ui.sqie_register_new.setCurrentIndex(0)
            ui.continuity_register_new.setCurrentIndex(0)
            ui.sourcing_register_new.setCurrentIndex(0)
            ui.planner_register_new.setCurrentIndex(0)
            ui.email_register_new.clear()

            funcoes.mostrar_toast(janela_principal, 3, "Success", "Supplier saved successfully.")

        except Exception as e:
            log_event(f"[ERROR SAVING SUPPLIER] {e}")
            funcoes.mostrar_toast(janela_principal, 2, "Error", f"An error occurred while saving: {e}")

       
    def atualizar_dados_supplier(self):
        # ATUALIZA SUPPLIER JÁ REGISTRADO
        try:
            supplier_id = ui.id_update.text()
            vendor_name = ui.vendor_update.text().strip().upper()
            supplier_name = ui.supplier_update.text().strip().upper()
            supplier_category = ui.category_update.currentText().strip()
            bu = ui.bu_update.currentText().strip()
            supplier_email = ui.email_update.toPlainText().strip()
            supplier_number = ui.supplier_number_update.text().strip()
            supplier_status = ui.supplier_status_update.currentText().strip()
            planner = ui.planner_update.currentText().strip()
            continuity = ui.continuity_update.currentText().strip()
            sourcing = ui.sourcing_update.currentText().strip()
            sqie = ui.sqie_update.currentText().strip()
            ssid = ui.ssid_update.text().strip()
            country = ui.country_update.text().strip().upper()
            region = ui.region_update.text().strip().upper()
            document = ui.document_update.text().strip().upper()
    

            if not vendor_name:
                funcoes.mostrar_toast(janela_principal,1,"Warning", "The 'Vendor' field cannot be empty.")
                return

            resultado = read("SELECT * FROM supplier_database_table WHERE supplier_id = ?", (supplier_id,))
            if not resultado:
                funcoes.mostrar_toast(janela_principal,1,"Information", f"The vendor '{vendor_name}' was not found in the database.")
                return


            update("""
                UPDATE supplier_database_table SET 
                    vendor_name = ?, supplier_category = ?, bu = ?, supplier_name = ?, 
                    supplier_email = ?, supplier_number = ?, supplier_status = ?, planner = ?, 
                    continuity = ?, sourcing = ?, sqie = ?, ssid = ?, 
                    country = ?, region = ?, document = ?
                WHERE supplier_id = ?
            """, (
                vendor_name, supplier_category, bu, supplier_name,
                supplier_email, supplier_number, supplier_status, planner,
                continuity, sourcing, sqie, ssid,
                country, region, document,
                supplier_id
            ))

            log_event(f"Updated supplier data for vendor '{vendor_name}' (ID {supplier_id})"); funcoes.preencher_table_log()

            funcoes.mostrar_toast(janela_principal,3,"Success", f"Supplier data for '{vendor_name}' was successfully updated.")

        except Exception as e:

            funcoes.mostrar_toast(janela_principal,2,"Error", f"An error occurred while updating supplier:\n{str(e)}")
            log_event(f"[ERROR] Failed to update supplier ID {supplier_id}: {str(e)}"); funcoes.preencher_table_log()


    def abrir_janela_select_supplier(self, origem):
        self.origem_botao_chamador = origem
        try:
            janela_select.show()

            mostrar_inativos = ui.checkBox_show_inactive.isChecked()

            resultados = read("SELECT * FROM supplier_database_table")

            IDX_ID = 0
            IDX_VENDOR = 1
            IDX_BU = 3
            IDX_SUPPLIER = 4
            IDX_STATUS = 7

            if not mostrar_inativos:
                resultados = [r for r in resultados if str(r[IDX_STATUS]).strip().lower() == "active"]

            resultados_ordenados = sorted(resultados, key=lambda x: x[IDX_VENDOR])

            table = ui_select.table_select_supplier
            table.setRowCount(len(resultados_ordenados))
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["ID", "Vendor", "Supplier", "BU", "Status"])

            header = table.horizontalHeader()
            header.setSectionResizeMode(0, header.Fixed)
            header.setSectionResizeMode(1, header.Stretch)  
            header.setSectionResizeMode(2, header.Fixed)
            header.setSectionResizeMode(3, header.Fixed)
            header.setSectionResizeMode(4, header.Fixed)

            table.setColumnWidth(0, 80)
            table.setColumnWidth(2, 80)
            table.setColumnWidth(3, 80)
            table.setColumnWidth(4, 80)

            for row_idx, row in enumerate(resultados_ordenados):
                valores = [
                    str(row[IDX_ID]),
                    str(row[IDX_VENDOR]),
                    str(row[IDX_SUPPLIER]),
                    str(row[IDX_BU]),
                    str(row[IDX_STATUS])
                ]

                for col_idx, valor in enumerate(valores):
                    item = QTableWidgetItem(valor)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                    if col_idx != 1:
                        item.setTextAlignment(Qt.AlignCenter)

                    table.setItem(row_idx, col_idx, item)

        except Exception as e:
            log_event(f"[Error] Loading suppliers failed: {e}"); funcoes.preencher_table_log()


    def preencher_table_log(self):
        logs = buscar_logs()
        ui.table_log.setRowCount(0)

        ui.table_log.setWordWrap(False)

        ui.table_log.setEditTriggers(QTableWidget.NoEditTriggers)

        for log in logs:
            row = ui.table_log.rowCount()
            ui.table_log.insertRow(row)

            ui.table_log.setItem(row, 0, QTableWidgetItem(log["date"]))
            ui.table_log.setItem(row, 1, QTableWidgetItem(log["time"]))
            ui.table_log.setItem(row, 2, QTableWidgetItem(log["user"]))

            item_event = QTableWidgetItem(log["event"])
            item_event.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  
            item_event.setToolTip(log["event"])  
            ui.table_log.setItem(row, 3, item_event)

        header = ui.table_log.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        header.resizeSection(0, 120)
        header.resizeSection(1, 120)
        header.resizeSection(2, 150)

        ui.table_log.setAlternatingRowColors(True)
        ui.table_log.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)


    def mostrar_info(self, checked=False):
    
        QMessageBox.information(
            None,
            "Information",
            "Developed by Rafael Negrão de Souza - Supply Continuity Intern\n"
            "rafael.negrao.souza@cummins.com\n"
            "AN62H"
        )


    def apagar_registro_selecionado(self):
        tabela = self.ui_main.tableDetails
        index = tabela.currentIndex()
        linha = index.row()

        if linha < 0:
            funcoes.mostrar_toast(janela_principal,1,"Warning", "No row selected.")
            return

        item_id = tabela.item(linha, 0)
        if not item_id:
            funcoes.mostrar_toast(janela_principal,1,"Warning", "Record ID not found.")
            return

        id_registro = item_id.text()

        resposta = QMessageBox.question(
            None,
            "Confirm",
            f"Are you sure you want to delete record ID {id_registro}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if resposta != QMessageBox.Yes:
            return

        try:
            delete("DELETE FROM supplier_score_records_table WHERE id = ?", (id_registro,))

            self.preencher_tabela_resultados()
            self.carregar_graficos()

            self.ui_main.tableDetails.horizontalHeader().setSectionResizeMode(
                self.ui_main.tableDetails.columnCount() - 1, QtWidgets.QHeaderView.Stretch
            )

        except Exception as e:
            funcoes.mostrar_toast(janela_principal,2,"Error", f"Failed to delete record:\n{e}")
            log_event(f"[ERROR] Failed to delete record: {e}")
            self.preencher_table_log()


    def buscar_dados_supplier_por_id(self, id_fornecedor):
        try:
            query = "SELECT * FROM supplier_database_table WHERE supplier_id = ?"
            resultados = read(query, (id_fornecedor,))
            return resultados[0] if resultados else None
        except Exception as e:
            log_event(f"[Error] Fetching supplier data by ID {id_fornecedor} failed: {e}"); funcoes.preencher_table_log()
            return None
        
    
    def selecionar_vendor_pelo_botao(self):
        linha = ui_select.table_select_supplier.currentRow()
        if linha < 0:
            log_event("[Warning] No row selected in supplier table."); funcoes.preencher_table_log()
            return

        item_id = ui_select.table_select_supplier.item(linha, 0)
        if not item_id:
            log_event("[Warning] Selected row has no ID item."); funcoes.preencher_table_log()
            return

        id_text = item_id.text()
        if not id_text or not id_text.isdigit():
            log_event(f"[Warning] Invalid supplier ID: '{id_text}'"); funcoes.preencher_table_log()
            return

        id_fornecedor = int(id_text)
        dados_tuple = self.buscar_dados_supplier_por_id(id_fornecedor)
        if not dados_tuple:
            log_event(f"[Warning] No supplier data found for ID: {id_fornecedor}"); funcoes.preencher_table_log()
            return

        colunas = [
            "supplier_id", "vendor_name", "supplier_category", "bu", "supplier_name", "supplier_email", "supplier_number","supplier_status", "planner", "continuity", "sourcing", "sqie", "ssid", "country", "region", "document", 
        ]
        dados = dict(zip(colunas, dados_tuple))

        funcoes_params = {
            "score": ["vendor_name", "bu","supplier_status","supplier_number"],
            
            "timeline": ["vendor_name",  "bu"],
            
            "update": ["vendor_name", "supplier_name", "bu", "supplier_category", "sqie", "sourcing","continuity", "planner","ssid", "country", "region", "document","supplier_status","supplier_number","supplier_email"],
            
            "email": ["vendor_name", "supplier_email"],
        }

        origem = self.origem_botao_chamador
        if origem in funcoes_params:
            args = [id_text] + [dados.get(param) for param in funcoes_params[origem]]
            getattr(self, f"preencher_{origem}")(*args)

        janela_select.close()


    def preencher_score(self,id, vendor, bu,status,number):
        ui.id_query.setText(str(id))
        ui.vendor_select.setText(vendor)
        ui.bu_query.setText(str(bu) if bu else "")
        ui.status_query.setText(str(status) if status else "")
        ui.number_query.setText(str(number) if number else "")


    def preencher_email(self,id, vendor,email):
        ui.id_mail.setText(str(id))
        ui.supplier_individual_mail.setText(vendor)
        ui.individual_recipients.setPlainText(email)
     
      
    def preencher_timeline(self,id, vendor, bu):
        ui.id_timeline.setText(id)
        ui.vendor_timeline.setText(vendor)
        ui.bu_query_2.setText(str(bu) if bu else "")
        self.carregar_graficos()
        funcoes.preencher_infos_supplier(id)


    def preencher_update(self,id, vendor, supplier, bu, category, sqie, sourcing, continuity,planner,ssid,country,region,document,status,number,email):
        ui.id_update.setText(id)
        ui.vendor_update.setText(vendor)
        ui.bu_update.setCurrentText(str(bu) if bu else "")
        ui.category_update.setCurrentText(str(category) if category else "")
        ui.sqie_update.setCurrentText(str(sqie) if sqie else "")
        ui.sourcing_update.setCurrentText(str(sourcing) if sourcing else "")
        ui.continuity_update.setCurrentText(str(continuity) if continuity else "")
        ui.supplier_update.setText(str(supplier) if supplier else "")
        ui.ssid_update.setText(str(ssid) if ssid else "")
        ui.country_update.setText(str(country) if country else "")
        ui.region_update.setText(str(region) if region else "")
        ui.document_update.setText(str(document) if document else "")
        ui.supplier_status_update.setCurrentText(str(status) if status else "")
        ui.supplier_number_update.setText(str(number) if number else "")
        ui.planner_update.setCurrentText(str(planner) if planner else "")
        ui.email_update.setPlainText(str(email) if email else "")


    def gerar_cards_risco(self, riscos):
        antigo_layout = ui.widget_risks.layout()
        if antigo_layout is not None:
            while antigo_layout.count():
                item = antigo_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
            QtWidgets.QWidget().setLayout(antigo_layout)

        altura_card = 130
        margem_extra = 30

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFixedHeight(altura_card + margem_extra)

        container_widget = QWidget()
        scroll.setWidget(container_widget)

        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.setContentsMargins(10, 10, 10, 10)

        for supplier_id, supplier_name, bu, q1, q2, q3, q4, media in riscos:
            card = QFrame()
            card.setFixedSize(250, altura_card)
            card.setStyleSheet("""
                QFrame {
                    background-color: #dddddd;
                    border-radius: 20px;
                }
            """)

            vbox = QVBoxLayout(card)
            vbox.setContentsMargins(12, 12, 12, 12)
            vbox.setSpacing(4)

            # Coletar trimestres válidos
            trimestres = []
            if q1 and int(q1) > 0:
                trimestres.append(('Q1', int(q1)))
            if q2 and int(q2) > 0:
                trimestres.append(('Q2', int(q2)))
            if q3 and int(q3) > 0:
                trimestres.append(('Q3', int(q3)))
            if q4 and int(q4) > 0:
                trimestres.append(('Q4', int(q4)))

            # Comparar últimos dois trimestres
            seta = ""
            if len(trimestres) >= 2:
                anterior = trimestres[-2][1]
                atual = trimestres[-1][1]
                if atual > anterior:
                    seta = "  ▲ "
                elif atual < anterior:
                    seta = "  🔻"
                elif atual == anterior:
                    seta = "  ▶"

            # Mostra valor principal com seta, se houver
            valor = QLabel(f"{int(media)}{seta}")
            valor.setFont(QFont("Arial", 20, QFont.Bold))
            vbox.addWidget(valor)

            nome = QLabel(supplier_name)
            nome.setFont(QFont("Arial", 9, QFont.Bold))
            nome.setWordWrap(False)
            nome.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            vbox.addWidget(nome)

            id_label = QLabel(f"ID: {supplier_id}")
            id_label.setFont(QFont("Arial", 8))
            vbox.addWidget(id_label)

            # Texto dos trimestres
            trimestres_texto = [f"{label}:{val}" for label, val in trimestres]
            trimestre = QLabel("  ".join(trimestres_texto))
            trimestre.setFont(QFont("Arial", 8))
            vbox.addWidget(trimestre)

            info_btn = QPushButton("ℹ")
            info_btn.setFixedSize(20, 20)
            info_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    font-family: "Times New Roman";
                    font-size: 18px;
                    font-weight: bold;
                    font-style: italic;
                    border: none;
                }
                QPushButton:hover {
                    color: blue;
                }
            """)
            info_btn.setCursor(Qt.PointingHandCursor)
            info_btn.clicked.connect(lambda _, sid=supplier_id: self.plotar_grafico_risco(sid))
            vbox.addWidget(info_btn, alignment=Qt.AlignRight)

            hbox.addWidget(card)

        container_widget.setLayout(hbox)

        layout_final = QVBoxLayout()
        layout_final.setContentsMargins(0, 0, 0, 0)
        layout_final.addWidget(scroll)

        ui.widget_risks.setLayout(layout_final)
        ui.widget_risks.setFixedHeight(altura_card + margem_extra)


    def plotar_grafico_risco(self, supplier_id):
        # Tornar visível e animar expansão do widget
        ui.widget_chart_risks_expand.setVisible(True)
        
        anim = QPropertyAnimation(ui.widget_chart_risks_expand, b"maximumHeight")
        anim.setDuration(100)  
        anim.setStartValue(0)
        anim.setEndValue(600)
        anim.start()
        self._anim_expand = anim  

        year = ui.year_risks.currentText().strip()
        rows = read("SELECT * FROM supplier_score_records_table WHERE supplier_id = ? ORDER BY year, month", (supplier_id,))

        if year and year.isdigit():
            ano_filtrado = int(year)
            rows = [row for row in rows if int(row[4]) == ano_filtrado]

        layout = ui.widget_chart_risks.layout()
        if layout is None:
            layout = QtWidgets.QVBoxLayout(ui.widget_chart_risks)
            ui.widget_chart_risks.setLayout(layout)
        else:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        if not rows:
            label = QLabel("No data available for this supplier")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 16px; color: red;")
            layout.addWidget(label)
            return

        fornecedor = read("SELECT vendor_name FROM supplier_database_table WHERE supplier_id = ?", (supplier_id,))
        nome_fornecedor = fornecedor[0][0] if fornecedor else f"Supplier {supplier_id}"

        meses_pt = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

        meses, valores, customdata = [], [], []
        for row in rows:
            mes, ano, total, comment = int(row[3]), int(row[4]), float(row[9]), row[10]
            meses.append(f"{meses_pt[mes]}/{str(ano)[2:]}")
            valores.append(total)
            customdata.append([comment if comment else "No comment"])

        soma = 0
        medias_total = []
        for i, v in enumerate(valores):
            soma += v
            medias_total.append(soma / (i + 1))

        meta = ui.target_criteria.value()

        textos = []
        for i, v in enumerate(valores):
            if i == 0:
                textos.append(f"{v:.1f}")
            else:
                anterior = valores[i - 1]
                variacao = ((v - anterior) / anterior) * 100 if anterior != 0 else 0
                seta = "🔺" if variacao > 0 else "🔻" if variacao < 0 else "➡️"
                textos.append(f"{v:.1f} ({seta} {abs(variacao):.1f}%)")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=meses,
            y=valores,
            mode='lines+markers',
            name="Score",
            marker=dict(size=6),
            line=dict(color="green", width=2, shape='spline'),
            text=textos,
            hovertemplate='<b>Score:</b> %{y}<br><b>Comment:</b> %{customdata[0]}<extra></extra>',
            customdata=customdata,
        ))

        fig.add_trace(go.Scatter(
            x=meses,
            y=medias_total,
            name="Avg Score",
            mode='lines',
            line=dict(color='blue', width=1, dash='dot')
        ))

        fig.add_shape(type='line', x0=0, x1=1, y0=meta, y1=meta,
                    xref='paper', yref='y',
                    line=dict(color='black', width=2, dash='dash'))

        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode='lines',
            line=dict(color='black', width=2, dash='dash'),
            name='Target'
        ))

        titulo = f"{supplier_id} - {nome_fornecedor}"
        titulo += f" ({year})" if year else " (All years)"

        fig.update_layout(
            title=dict(
                text=titulo,
                x=0.5,
                pad=dict(t=20, b=20)
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="black"),
            margin=dict(l=20, r=20, t=80, b=60),
            yaxis=dict(
                range=[0, 400],
                fixedrange=True,
                showgrid=True,
                gridcolor='rgba(200,200,200,0.3)',
                gridwidth=1,
                zeroline=True,
                zerolinecolor='rgba(200,200,200,0.3)',
                zerolinewidth=1
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(200,200,200,0.3)',
                gridwidth=1
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        html = (
            "<style>body { background-color: rgba(0,0,0,0); margin: 0; }</style>"
            "<script>window.PlotlyConfig = {displayModeBar: false};</script>"
            + pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
        )

        web_view = QtWebEngineWidgets.QWebEngineView()
        web_view.setStyleSheet("background: transparent")
        web_view.setHtml(html, QtCore.QUrl("about:blank"))
        layout.addWidget(web_view)


    def fechar_grafico_risco(self):
        ui.widget_chart_risks_expand.setVisible(False)


    def verificar_riscos(self):
        year = ui.year_risks.currentText().strip()
        meta = ui.target_criteria.value()

        filtro_ano = "WHERE s.year = ?" if year else ""
        params = (year, meta) if year else (meta,)

        query_base = f"""
            SELECT 
                s.supplier_id, 
                s.supplier_name, 
                sl.bu,
                AVG(CASE WHEN s.month IN (1,2,3) THEN CAST(s.total_score AS FLOAT) END) AS Q1,
                AVG(CASE WHEN s.month IN (4,5,6) THEN CAST(s.total_score AS FLOAT) END) AS Q2,
                AVG(CASE WHEN s.month IN (7,8,9) THEN CAST(s.total_score AS FLOAT) END) AS Q3,
                AVG(CASE WHEN s.month IN (10,11,12) THEN CAST(s.total_score AS FLOAT) END) AS Q4,
                AVG(CAST(s.total_score AS FLOAT)) AS media_score
            FROM supplier_score_records_table s
            JOIN supplier_database_table sl ON s.supplier_id = sl.supplier_id
            {filtro_ano}
            GROUP BY s.supplier_id, s.supplier_name, sl.bu
            HAVING media_score {{op}} ?
        """

        query_riscos = query_base.format(op='<')
        query_ok = query_base.format(op='>=')

        riscos = read(query_riscos, params)
        ok = read(query_ok, params)

        ui.total_risks.setText(str(len(riscos)))
        ui.total_geral2.setText(f"/{len(riscos) + len(ok)}")
        self.fechar_grafico_risco()

        self.gerar_cards_risco(riscos)


    def comparar_senha_edicao_criteria(self) -> bool:

        dialog = QDialog()
        dialog.setWindowTitle("Password Verification")
        dialog.setFixedWidth(400)

        layout = QVBoxLayout(dialog)
        label = QLabel("Enter your password:")
        campo = QLineEdit()
        campo.setEchoMode(QLineEdit.Password)
        campo.setPlaceholderText("Password")

        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        layout.addWidget(label)
        layout.addWidget(campo)
        layout.addWidget(botoes)

        resultado = {"valido": False}

        def ao_clicar_ok():
            senha = campo.text().strip()
            if not senha:
                funcoes.mostrar_toast(janela_principal,2,"Input Error", "Please enter a password.")
                return

            # Consulta SQL para verificar senha (ajuste conforme seu schema)
            query = "SELECT 1 FROM criteria_password_table WHERE password = ? LIMIT 1"
            res = read(query, (senha,))
            if res:
                resultado["valido"] = True
                dialog.accept()

                # Habilita os campos
                ui.quality_packege_criteria.setEnabled(True)
                ui.quality_pickup_criteria.setEnabled(True)
                ui.target_criteria.setEnabled(True)
                ui.nil_criteria.setEnabled(True)
                ui.otif_criteria.setEnabled(True)
                ui.btn_unlock_criteria_edit.setText("🔓")
            else:
                funcoes.mostrar_toast(janela_principal,2,"Access Denied", "Incorrect password.")

        botoes.accepted.connect(ao_clicar_ok)
        botoes.rejected.connect(dialog.reject)

        dialog.exec_()
        return resultado["valido"]


    def ocultar_menu():
        global em_animacao_sidebar
        if em_animacao_sidebar:
            return  # Bloqueia reentrada
        em_animacao_sidebar = True

        largura_atual = ui.sidebar.width()
        largura_aberta = 180
        largura_fechada = 50
        passo = 5
        delay_ms = 1

        if largura_atual > largura_fechada:
            for largura in range(largura_atual, largura_fechada - 1, -passo):
                ui.sidebar.setFixedWidth(largura)
                tamanho = int(Functions.mapear_intervalo(largura, largura_fechada, largura_aberta, 50, 180))
                ui.label_imagem_logo.setFixedSize(tamanho, tamanho)
                Functions.atualizar_logo()
                loop = QEventLoop()
                QTimer.singleShot(delay_ms, loop.quit)
                loop.exec_()
            ui.sidebar.setFixedWidth(largura_fechada)
            ui.label_imagem_logo.setFixedSize(40, 40)
            ui.label_version.setVisible(False)
            ui.label_version_number.setVisible(False)
        else:
            for largura in range(largura_atual, largura_aberta + 1, passo):
                ui.sidebar.setFixedWidth(largura)
                tamanho = int(Functions.mapear_intervalo(largura, largura_fechada, largura_aberta, 50, 180))
                ui.label_imagem_logo.setFixedSize(tamanho, tamanho)
                Functions.atualizar_logo()
                loop = QEventLoop()
                QTimer.singleShot(delay_ms, loop.quit)
                loop.exec_()
            ui.sidebar.setFixedWidth(largura_aberta)
            ui.label_imagem_logo.setFixedSize(180, 180)
            ui.label_version.setVisible(True)
            ui.label_version_number.setVisible(True)

        em_animacao_sidebar = False  


    def fechar_grafico_risco(self):
        widget = ui.widget_chart_risks_expand
        altura_atual = widget.height()
        altura_final = 0
        passo = 10
        delay_ms = 1

        if altura_atual <= altura_final:
            widget.setVisible(False)
            return

        for altura in range(altura_atual, altura_final - 1, -passo):
            widget.setMaximumHeight(altura)
            loop = QEventLoop()
            QTimer.singleShot(delay_ms, loop.quit)
            loop.exec_()

        widget.setMaximumHeight(0)
        widget.setVisible(False)

        layout = ui.widget_chart_risks.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                widget_item = item.widget()
                if widget_item:
                    widget_item.deleteLater()


    def ocultar_right_sidebar():
        global em_animacao_right_sidebar
        if em_animacao_right_sidebar:
            return  
        em_animacao_right_sidebar = True

        largura_atual = ui.right_sidebar.width()
        largura_aberta = 300
        largura_fechada = 0
        passo = 20
        delay_ms = 1
        id = ui.id_timeline.text()

        if largura_atual > largura_fechada:
            funcoes.preencher_infos_supplier(id)
            for largura in range(largura_atual, largura_fechada - 1, -passo):
                ui.right_sidebar.setFixedWidth(largura)
                loop = QEventLoop()
                QTimer.singleShot(delay_ms, loop.quit)
                loop.exec_()
            ui.right_sidebar.setFixedWidth(largura_fechada)
        else:
            funcoes.preencher_infos_supplier(id)
            for largura in range(largura_atual, largura_aberta + 1, passo):
                ui.right_sidebar.setFixedWidth(largura)
                loop = QEventLoop()
                QTimer.singleShot(delay_ms, loop.quit)
                loop.exec_()
            ui.right_sidebar.setFixedWidth(largura_aberta)

        em_animacao_right_sidebar = False  


    def preencher_infos_supplier(self, id):
        try:
            resultado = read(
                "SELECT supplier_name, supplier_category, planner, continuity, sourcing, sqie, supplier_number, supplier_email, supplier_status FROM supplier_database_table WHERE supplier_id = ?", 
                (id,)
            )

            if not resultado:
                ui.info_field.setPlainText("")
                return

            (supplier_name, supplier_category, planner, continuity, 
            sourcing, sqie, supplier_number, supplier_email, supplier_status) = resultado[0]

            def buscar_info(table, name):
                if not name or not name.strip():
                    return None
                dados = read(f"SELECT alias, email FROM {table} WHERE name = ?", (name.strip(),))
                return dados[0] if dados else None

            seções = []

            # Supplier Info (sempre exibido)
            seções.append(f"""
            <b>Supplier Info</b><br>
            Name: {supplier_name}<br>
            Category: {supplier_category}<br>
            Number: {supplier_number}<br>
            Status: {supplier_status}<br><br>
            """)

            if planner.strip():
                info = buscar_info("planner_table", planner)
                if info:
                    planner_alias, planner_email = info
                    seções.append(f"""
                    <b>Planner</b><br>
                    Name : {planner}<br>
                    WWID: {planner_alias}<br>
                    Email: {planner_email}<br><br>
                    """)

            if continuity.strip():
                info = buscar_info("continuity_table", continuity)
                if info:
                    continuity_alias, continuity_email = info
                    seções.append(f"""
                    <b>Continuity</b><br>
                    Name : {continuity}<br>
                    WWID: {continuity_alias}<br>
                    Email: {continuity_email}<br><br>
                    """)

            if sourcing.strip():
                info = buscar_info("sourcing_table", sourcing)
                if info:
                    sourcing_alias, sourcing_email = info
                    seções.append(f"""
                    <b>Sourcing</b><br>
                    Name : {sourcing}<br>
                    WWID: {sourcing_alias}<br>
                    Email: {sourcing_email}<br><br>
                    """)

            if sqie.strip():
                info = buscar_info("sqie_table", sqie)
                if info:
                    sqie_alias, sqie_email = info
                    seções.append(f"""
                    <b>SQIE</b><br>
                    Name : {sqie}<br>
                    WWID: {sqie_alias}<br>
                    Email: {sqie_email}<br><br>
                    """)

            if supplier_email and any(email.strip() for email in supplier_email.split(";")):
                email_list = [email.strip() for email in supplier_email.split(";") if email.strip()]
                email_formatado = "<br>".join(f"&nbsp;&nbsp;• {email}" for email in email_list)
                seções.append(f"""
                <b>Supplier Email</b><br>
                {email_formatado}
                """)

            ui.info_field.setHtml("".join(seções))

        except Exception as e:
            log_event(f"[ERROR] Failed to fill supplier info: {str(e)}")
            self.preencher_table_log()
            ui.info_field.setPlainText("An error occurred while retrieving supplier information.")


    def atualizar_logo():
        ui.label_imagem_logo.setScaledContents(True)
        pixmap = QPixmap(":/imagens/logo.png")  # caminho no qrc
        if not pixmap.isNull():
            ui.label_imagem_logo.setPixmap(
                pixmap.scaled(
                    ui.label_imagem_logo.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )


    def mapear_intervalo(valor, entrada_min, entrada_max, saida_min, saida_max):
        """Função auxiliar para interpolar valores entre dois intervalos"""
        if entrada_max == entrada_min:
            return saida_min
        return saida_min + (valor - entrada_min) * (saida_max - saida_min) / (entrada_max - entrada_min)


    def salvar_preferencia_checkbox(self):
        try:
            estado = ui.checkBox_show_inactive.isChecked()

            pasta_config = Path(os.getenv("APPDATA")) / "MeuSistema"
            pasta_config.mkdir(parents=True, exist_ok=True)

            caminho_config = pasta_config / "config.json"

            config = {}
            if caminho_config.exists():
                with open(caminho_config, "r") as f:
                    config = json.load(f)

            config["show_inactive"] = estado  

            with open(caminho_config, "w") as f:
                json.dump(config, f)

        except Exception as e:
            log_event(f"[Error] Saving checkbox preference failed: {e}")


    def carregar_preferencia_checkbox(self):
        try:


            caminho_config = Path(os.getenv("APPDATA")) / "MeuSistema" / "config.json"

            if caminho_config.exists():
                with open(caminho_config, "r") as f:
                    config = json.load(f)
                    estado = config.get("show_inactive", False)
                    ui.checkBox_show_inactive.setChecked(estado)

        except Exception as e:
            log_event(f"[Error] Loading checkbox preference failed: {e}")


    def salvar_preferencia_login(self):
        try:
            pasta_config = Path(os.getenv("APPDATA")) / "MeuSistema"
            pasta_config.mkdir(parents=True, exist_ok=True)
            caminho_config = pasta_config / "config.json"

            config = {}
            if caminho_config.exists():
                with open(caminho_config, "r") as f:
                    config = json.load(f)

            lembrar = ui_login.checkBox_remember_login.isChecked()
            config["remember_login"] = lembrar

            if lembrar:
                config["wwid"] = ui_login.wwid_user.text()
                config["password"] = ui_login.password_login.text()
            else:
                # Se desmarcar, apaga do arquivo
                config.pop("wwid", None)
                config.pop("password", None)

            with open(caminho_config, "w") as f:
                json.dump(config, f)

        except Exception as e:
            log_event(f"[Error] Saving login preference failed: {e}")


    def carregar_preferencia_login(self):
        try:

            caminho_config = Path(os.getenv("APPDATA")) / "MeuSistema" / "config.json"

            if caminho_config.exists():
                with open(caminho_config, "r") as f:
                    config = json.load(f)

                lembrar = config.get("remember_login", False)
                ui_login.checkBox_remember_login.setChecked(lembrar)

                if lembrar:
                    ui_login.wwid_user.setText(config.get("wwid", ""))
                    ui_login.password_login.setText(config.get("password", ""))

        except Exception as e:
            log_event(f"[Error] Loading login preference failed: {e}")


    def evento_ao_abrir(self):
        self.carregar_todos_sqie()
        self.carregar_todos_continuity()
        self.carregar_todos_sourcing()
        self.carregar_todos_planner()
        self.carregar_todos_categories()
        self.carregar_todos_bus()
        self.carregar_criterios_dos_campos()
        self.preencher_table_log()
        self.carregar_preferencia_checkbox()


    def evento_ao_fechar(self, event):
        janela_select.close()
        
        event.accept()
    







##########################################################################################################################################
##########################################################################################################################################
##########################################################################################################################################
##########################################################################################################################################


# ---- INICIALIZAÇÃO ----
app = QtWidgets.QApplication(sys.argv)

janela_principal = QtWidgets.QMainWindow()
janela_login = QtWidgets.QMainWindow()
janela_select = QtWidgets.QMainWindow()


ui = Ui_MainWindow()
ui.setupUi(janela_principal)

ui_login = Ui_LoginWindow()
ui_login.setupUi(janela_login)


ui_select = Ui_windowSelectSupplier()
ui_select.setupUi(janela_select)


funcoes = Functions(ui_login, janela_login, janela_principal, ui,ui_select)
funcoes.evento_ao_abrir()


janela_principal.closeEvent = funcoes.evento_ao_fechar


# Botões
ui.btn_home.clicked.connect(lambda: Functions.mudar_pagina(0))
ui.btn_score.clicked.connect(lambda: Functions.mudar_pagina(1))
ui.btn_timeline.clicked.connect(lambda: Functions.mudar_pagina(2))
ui.btn_risks.clicked.connect(lambda: Functions.mudar_pagina(3));funcoes.verificar_riscos()
ui.btn_configs.clicked.connect(lambda: Functions.mudar_pagina(4))
ui.btn_ocultar.clicked.connect(lambda: Functions.ocultar_menu())
ui.btn_show_info.clicked.connect(lambda:Functions.ocultar_right_sidebar())
ui.btn_close_right_sidebar.clicked.connect(lambda: Functions.ocultar_right_sidebar())


ui.btn_save_new_score.clicked.connect(Functions.salvar_score)
ui.btn_update_supplier.clicked.connect(funcoes.atualizar_dados_supplier)
ui.btn_info.clicked.connect(funcoes.mostrar_info)
ui.btn_update_criteria.clicked.connect(lambda: funcoes.atualizar_criterios_no_banco())
ui.btn_vendor_score.clicked.connect(lambda: funcoes.abrir_janela_select_supplier("score"))
ui.btn_vendor_timeline.clicked.connect(lambda: funcoes.abrir_janela_select_supplier("timeline"))
ui.btn_vendor_register.clicked.connect(lambda: funcoes.abrir_janela_select_supplier("update"))
ui_login.btn_login.clicked.connect(lambda: funcoes.iniciar_splash())
ui.btn_fechar_grafico_risks.clicked.connect(lambda: funcoes.fechar_grafico_risco())
ui.btn_register_new_supplier.clicked.connect(lambda: funcoes.salvar_novo_supplier())
ui.btn_save_new_user.clicked.connect(lambda: funcoes.adicionar_novo_usuario())

ui.year_risks.currentTextChanged.connect(lambda: funcoes.verificar_riscos())
ui.year_timeline.currentTextChanged.connect(lambda: funcoes.carregar_graficos())


ui.btn_clear_register.clicked.connect(funcoes.apagar_registro_selecionado)
ui.btn_add_continuity.clicked.connect(funcoes.adicionar_continuity)
ui.btn_add_sourcing.clicked.connect(funcoes.adicionar_sourcing)
ui.btn_add_sqie.clicked.connect(funcoes.adicionar_sqie)
ui.btn_clear_new_register.clicked.connect(funcoes.apagar_todos_campos_register)
ui.btn_clear_score.clicked.connect(funcoes.apagar_todos_campos_query)
ui.btn_add_category.clicked.connect(funcoes.adicionar_category)
ui.btn_add_bu.clicked.connect(funcoes.adicionar_bu)
ui.btn_unlock_criteria_edit.clicked.connect(funcoes.comparar_senha_edicao_criteria)
ui.btn_generate_full_list.clicked.connect(funcoes.gerar_lista_nota_cheia)
ui.btn_group_input.clicked.connect(funcoes.preencher_tabela_grupo)
ui.btn_edit_user.clicked.connect(funcoes.atualizar_senha)

# Alteração nos campos
ui.quality_package_input.textChanged.connect(lambda: Functions.total_score_calculate())
ui.quality_pickup_input.textChanged.connect(lambda: Functions.total_score_calculate())
ui.nil_input.textChanged.connect(lambda: Functions.total_score_calculate())
ui.otif_input.textChanged.connect(lambda: Functions.total_score_calculate())
ui.tabWidget.currentChanged.connect(lambda index: funcoes.carregar_graficos() if index == 1 else None)
ui_select.btn_select_vendor.clicked.connect(lambda:funcoes.selecionar_vendor_pelo_botao())
ui_select.table_select_supplier.cellDoubleClicked.connect(lambda:funcoes.selecionar_vendor_pelo_botao())
ui.checkBox_show_inactive.clicked.connect(lambda: funcoes.salvar_preferencia_checkbox())
ui_login.checkBox_remember_login.clicked.connect(lambda:funcoes.salvar_preferencia_login())
funcoes.carregar_preferencia_login()
em_animacao_sidebar = False
em_animacao_right_sidebar = False


ui.tableDetails.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
janela_login.setWindowFlags(QtCore.Qt.FramelessWindowHint)


janela_principal.setWindowFlags(
    QtCore.Qt.Window |
    QtCore.Qt.WindowMinimizeButtonHint |
    QtCore.Qt.WindowMaximizeButtonHint |
    QtCore.Qt.WindowCloseButtonHint
)

janela_login.show()

sys.exit(app.exec_())