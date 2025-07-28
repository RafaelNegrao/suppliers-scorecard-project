import sys
import datetime
import getpass
import plotly.graph_objects as go
import plotly.io as pio
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets
from PyQt5.QtWidgets import (
    QLabel, QMessageBox, QTableWidgetItem, QHeaderView, QVBoxLayout,
    QDialog, QLineEdit, QDialogButtonBox, QTableWidget,
    QAbstractItemView, QProgressBar,QTextEdit, QApplication
)
from PyQt5.QtCore import Qt, QEventLoop, QTimer
from PyQt5.QtGui import QIcon, QColor, QPixmap
from selectSupplier import Ui_windowSelectSupplier
from Interface import Ui_MainWindow
from loginWindow import Ui_LoginWindow
from crud import read, create, update, delete, log_event, buscar_logs
import os, json
from pathlib import Path






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




    def salvar_novo_supplier(self, _=None):
        vendor = ui.vendor_register_new.text().strip().upper()
        supplier = ui.supplier_register.text().strip().upper()
        bu = ui.bu_register_new.currentText().strip()
        category = ui.new_category.currentText().strip()
        sqie = ui.sqie_register_new.currentText().strip()
        planner = ui.planner_register_new.currentText().strip()
        sourcing = ui.sourcing_register_new.currentText().strip()
        continuity = ui.continuity_register_new.currentText().strip()
        ssid = ui.ssid_register_new.text().strip().upper()
        country = ui.country_register_new.text().strip().upper()
        region = ui.region_register_new.text().strip().upper()
        document = ui.document_register_new.text().strip().upper()
        supplier_number = ui.new_supplier_number.text()
        supplier_mail = ui.new_supplier_number.text()

        campos_obrigatorios = {
            "Vendor": vendor,
            "Supplier": supplier,
            "BU": bu,
            "Planner": planner,
            "Category": category,
            "SQIE": sqie,
            "Sourcing": sourcing,
            "Continuity": continuity,
            "SSID": ssid,
            "Country": country,
            "Region": region,
            "Document": document,
            "Supplier_number": supplier_number,
            "Supplier_mail": supplier_mail
        }

        for nome_campo, valor in campos_obrigatorios.items():
            if not valor:
                QMessageBox.warning(None, "Required Field", f"The field '{nome_campo}' is required.")
                return

        try:
            # Usando o CRUD genérico
            create("supplier_database_table", {
                "vendor_name": vendor,
                "bu": bu,
                "supplier_name": supplier,
                "supplier_mail": supplier_mail,
                "supplier_number": supplier_number,
                "supplier_category": category,
                "planner": planner,
                "continuity": continuity,
                "sourcing": sourcing,
                "sqie": sqie,
                "category": category,
                "ssid": ssid,
                "country": country,
                "region": region,
                "document": document,

            })

            QMessageBox.information(None, "Success", "Supplier saved successfully.")

            # Zera os campos
            ui.vendor_register_new.setText("")
            ui.supplier_register.setText("")
            ui.bu_register_new.setCurrentIndex(0)
            ui.new_category.setCurrentIndex(0)
            ui.sqie_register_new.setCurrentIndex(0)
            ui.sourcing_register_new.setCurrentIndex(0)
            ui.continuity_register_new.setCurrentIndex(0)
            ui.ssid_register_new.setText("")
            ui.country_register_new.setText("")
            ui.region_register_new.setText("")
            ui.document_register_new.setText("")   

            # Atualiza vendor_register
            self.carregar_fornecedores_do_banco()
            self.verificar_riscos()
            #ui.vendor_register.blockSignals(True)
            ui.vendor_register.clear()
            #ui.vendor_register.addItems(fornecedores)
            #ui.vendor_register.blockSignals(False)

        except Exception as erro:
            QMessageBox.critical(None, "Error", f"Error while saving supplier:\n{erro}")


    def iniciar_splash(self):
        try:
            self.ui_login.btn_login.setEnabled(False)

            wwid_digitado = self.ui_login.wwid_user.text().strip()
            senha_digitada = self.ui_login.password_login.text().strip()

            if not wwid_digitado or not senha_digitada:
                QMessageBox.warning(self.janela_login, "Login Failed", "Please enter both WWID and password.")
                self.ui_login.btn_login.setEnabled(True)  
                return

            resultado = read("SELECT user_wwid, user_password, user_privilege FROM users_table WHERE user_wwid = ?", (wwid_digitado,))

            if not resultado:
                QMessageBox.critical(self.janela_login, "Login Failed", f"WWID '{wwid_digitado}' not found.")
                self.ui_login.btn_login.setEnabled(True)  
                return

            wwid_banco, senha_banco, privilegio = resultado[0]

            if senha_digitada != senha_banco:
                QMessageBox.critical(self.janela_login, "Login Failed", "Incorrect password.")
                self.ui_login.btn_login.setEnabled(True)
                return

            self.usuario_logado = {
                "wwid": wwid_banco,
                "privilege": privilegio
            }

            self.ui_login.barra_progresso.setValue(0)
            self.tempo_inicial = QtCore.QElapsedTimer()
            self.tempo_inicial.start()
            self.duracao_total = 2000  

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
            QMessageBox.critical(self.janela_login, "Error", f"An unexpected error occurred:\n{str(e)}")
            log_event(f"[Login Error] {str(e)}")
            funcoes.preencher_table_log()
            self.ui_login.btn_login.setEnabled(True)  


        except Exception as e:
            QMessageBox.critical(self.janela_login, "Error", f"An unexpected error occurred:\n{str(e)}")
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
                QMessageBox.warning(self.janela_principal, "Invalid Input", "Please fill in WWID, new password, and privilege.")
                return

            resultado = read("SELECT 1 FROM users_table WHERE user_wwid = ?", (wwid,))
            if not resultado:
                QMessageBox.warning(self.janela_principal, "User Not Found", f"No user found with WWID '{wwid}'.")
                return

            update(
                "UPDATE users_table SET user_password = ?, user_privilege = ? WHERE user_wwid = ?",
                (nova_senha, novo_privilegio, wwid)
            )

            QMessageBox.information(
                self.janela_principal,
                "Success",
                f"Password and privilege updated successfully for WWID '{wwid}'."
            )

        except Exception as e:
            QMessageBox.critical(self.janela_principal, "Error", f"An error occurred while updating data:\n{str(e)}")
            log_event(f"[Update Password/Privilege Error] {str(e)}")
            funcoes.preencher_table_log()


    def atualizar_media_12_meses(self):
        id = ui.id_timeline.text().strip()
        if not id:
            ui.average_12month.setText("")
            return

        registros = read("SELECT * FROM supplier_score_records_table WHERE supplier_id = ?", (id,))
        if not registros:
            ui.average_12month.setText("")
            return

        try:
            ordenado = sorted(registros, key=lambda r: (int(r[4]), int(r[3])), reverse=True)
            max_ano, max_mes = int(ordenado[0][4]), int(ordenado[0][3])
        except Exception as e:
            print(f"Erro ao identificar último ano/mês: {e}")
            ui.average_12month.setText("")
            return

        data_base = QtCore.QDate(max_ano, max_mes, 1)
        ultimos_12_meses = [(data_base.addMonths(-i).year(), data_base.addMonths(-i).month()) for i in range(11, -1, -1)]

        dados = {}
        for row in registros:
            try:
                ano = int(row[4])
                mes = int(row[3])
                score = float(row[9])
                dados[(ano, mes)] = score
            except:
                pass

        valores = [dados.get((ano, mes), 0) for ano, mes in ultimos_12_meses]
        divisor = len([v for v in valores if v > 0]) or 1
        media_12_meses = sum(valores) / divisor

        ui.average_12month.setText(f" {int(media_12_meses)}")


    def atualizar_media_6_meses(self):
        id = ui.id_timeline.text().strip()
        if not id:
            ui.average_6month.setText("")
            return

        registros = read("SELECT * FROM supplier_score_records_table WHERE supplier_id = ?", (id,))
        if not registros:
            ui.average_6month.setText("")
            return

        try:
            ordenado = sorted(registros, key=lambda r: (int(r[4]), int(r[3])), reverse=True)
            max_ano, max_mes = int(ordenado[0][4]), int(ordenado[0][3])
        except Exception as e:
            print(f"Erro ao identificar último ano/mês: {e}")
            ui.average_6month.setText("")
            return

        data_base = QtCore.QDate(max_ano, max_mes, 1)
        ultimos_6_meses = [(data_base.addMonths(-i).year(), data_base.addMonths(-i).month()) for i in range(5, -1, -1)]

        dados = {}
        for row in registros:
            try:
                ano = int(row[4])
                mes = int(row[3])
                score = float(row[9])
                dados[(ano, mes)] = score
            except:
                pass

        valores = [dados.get((ano, mes), 0) for ano, mes in ultimos_6_meses]
        divisor = len([v for v in valores if v > 0]) or 1
        media_6_meses = sum(valores) / divisor

        ui.average_6month.setText(f" {int(media_6_meses)}")


    def atualizar_medias_trimestrais(self):
        id = ui.id_timeline.text().strip()
        if not id:
            ui.average_q1.setText("")
            ui.average_q2.setText("")
            ui.average_q3.setText("")
            ui.average_q4.setText("")
            return

        registros = read("SELECT * FROM supplier_score_records_table WHERE supplier_id = ?", (id,))
        if not registros:
            ui.average_q1.setText("")
            ui.average_q2.setText("")
            ui.average_q3.setText("")
            ui.average_q4.setText("")
            return

        from collections import defaultdict
        import datetime

        ano_atual = datetime.datetime.now().year
        trimestres = defaultdict(list)

        for row in registros:
            try:
                ano = int(row[4])
                mes = int(row[3])
                score = float(row[9])

                if ano == ano_atual:
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
                return ""
            return str(int(sum(valores) / len(valores)))

        ui.average_q1.setText(f" {calcular_media(trimestres['q1'])}")
        ui.average_q2.setText(f" {calcular_media(trimestres['q2'])}")
        ui.average_q3.setText(f" {calcular_media(trimestres['q3'])}")
        ui.average_q4.setText(f" {calcular_media(trimestres['q4'])}")


    def atualizar_media_geral(self):
        id = ui.id_timeline.text().strip()
        if not id:
            ui.overhall_average.setText("")
            return

        registros = read("SELECT * FROM supplier_score_records_table WHERE supplier_id = ?", (id,))
        if not registros:
            ui.overhall_average.setText("")
            return

        try:
            valores = [float(row[9]) for row in registros]  # total_score no índice 9
            media_geral = sum(valores) / len(valores)
        except Exception as e:
            print(f"Erro ao calcular média geral: {e}")
            ui.overhall_average.setText("")
            return

        ui.overhall_average.setText(f" {int(media_geral)}")


    def total_score_possivel(self):
        total = (int(ui.quality_packege_criteria.value())*10) + \
                (int(ui.nil_criteria.value())*10) + \
                (int(ui.otif_criteria.value())*10) + \
                (int(ui.quality_pickup_criteria.value())*10)
        
        total_str = f" /{total}"


    def criar_grafico_coluna(self, container_widget):
        id = self.ui_main.id_timeline.text().strip()
        if not id:
            return

        # Consulta ajustada
        rows = read("SELECT * FROM supplier_score_records_table WHERE supplier_id = ? ORDER BY year, month", (id,))

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

        # month = [3], year = [4], total_score = [9], comment = [10]
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
        if not id_fornecedor:
            ui.tableDetails.clearContents()
            ui.tableDetails.setRowCount(0)
            return

        query = """
            SELECT * 
            FROM supplier_score_records_table 
            WHERE supplier_id = ?
        """
        rows = read(query, (id_fornecedor,))
        if not rows:
            ui.tableDetails.clearContents()
            ui.tableDetails.setRowCount(0)
            return

        # Ordenar manualmente pela data (ano e mês), do mais novo para o mais antigo
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
            # row = (row_id, supplier_id, supplier_name, month, year, quality_package, quality_pickup, nil, otif, total_score, comment, register_date, created_by, updated_at, changed_by)
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
        self.atualizar_media_6_meses()
        self.atualizar_medias_trimestrais()
        self.atualizar_media_geral()
        self.preencher_tabela_resultados()
        self.total_score_possivel()
        

    def mudar_pagina(indice):
        ui.tabWidget.setCurrentIndex(indice)
        
        if ui.tabWidget.currentIndex() == 4:
            funcoes.verificar_riscos()
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

        # Primeiro aplica o estilo dos não selecionados (reset)
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

        # Estilo para o botão **selecionado**
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

            # Verifica se os campos obrigatórios foram preenchidos
            if not id_fornecedor or fornecedor == "" or mes == "" or ano == "":
                QMessageBox.warning(janela_principal, "Warning", "Supplier ID, name, month, and year are required to save the score.")
                log_event("Error while saving score: Missing required fields."); funcoes.preencher_table_log()
                funcoes.preencher_table_log()
                return

            # Verifica se já existe um registro com esse supplier_id, ano e mês
            existe = read(
                "SELECT 1 FROM supplier_score_records_table WHERE supplier_id = ? AND month = ? AND year = ?",
                (id_fornecedor, mes, ano)
            )

            if existe:
                # Se já existir, pergunta ao usuário se ele quer sobrescrever (atualizar)
                resposta = QMessageBox.question(
                    janela_principal,
                    "Duplicate Entry",
                    "This supplier already has a score registered for this month and year.\nDo you want to overwrite it?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if resposta == QMessageBox.No:
                    return

                # Atualiza o registro existente
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
                QMessageBox.information(janela_principal, "Success", "Score updated successfully.")
            else:
                # Insere novo registro, pois não existe ainda
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
                QMessageBox.information(janela_principal, "Success", "Score saved successfully.")

            # Limpa todos os campos da interface após salvar
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
            QMessageBox.critical(janela_principal, "Error", f"An error occurred while saving:\n{str(e)}")
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
                QMessageBox.critical(janela_principal, "Error", "One or more scoring criteria are missing in criteria_table.")
                log_event("Error while generating scores: Missing criteria."); funcoes.preencher_table_log()
                return

            fornecedores = read("SELECT supplier_id, vendor_name, supplier_status FROM supplier_database_table")

            if not fornecedores:
                QMessageBox.information(janela_principal, "Info", "No suppliers found in database.")
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
            QMessageBox.critical(janela_principal, "Error", f"An error occurred while generating scores:\n{str(e)}")
            log_event(f"Error while generating scores: {str(e)}"); funcoes.preencher_table_log()


    def preencher_tabela_grupo(self):
        try:
            mes = ui.month_group_input.currentText().strip()
            ano = ui.year_group_input.currentText().strip()

            if not mes or not ano:
                QMessageBox.warning(janela_principal, "Warning", "Month and year must be selected to load data.")
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
            QMessageBox.critical(janela_principal, "Error", f"An error occurred while loading table data:\n{str(e)}")
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
        name = ui.new_sqie.text().strip()
        alias = ui.new_alias_sqie.text().strip().upper()
        email = ui.new_sqie_email.text().strip()
        registered_by = getpass.getuser()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not name or not alias or not email:
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
                    QMessageBox.information(None, "SQIE Updated", f"SQIE '{alias}' updated successfully.")
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
            QMessageBox.information(None, "SQIE Added", f"SQIE '{alias}' added successfully.")
            ui.new_sqie.clear()
            ui.new_alias_sqie.clear()
            ui.new_sqie_email.clear()
            self.preencher_table_log()

        except Exception as e:
            log_event(f"[ERROR] Failed to add/edit SQIE: {str(e)}")
            self.preencher_table_log()


    def adicionar_continuity(self):
        name = ui.new_continuity.text().strip()
        alias = ui.new_alias_continuity.text().strip().upper()
        email = ui.new_continuity_email.text().strip()
        registered_by = getpass.getuser()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not name or not alias or not email:
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
                    QMessageBox.information(None, "Continuity Updated", f"Continuity '{alias}' updated successfully.")
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
            QMessageBox.information(None, "Continuity Added", f"Continuity '{alias}' added successfully.")
            ui.new_continuity.clear()
            ui.new_alias_continuity.clear()
            ui.new_continuity_email.clear()
            self.preencher_table_log()

        except Exception as e:
            log_event(f"[ERROR] Failed to add/edit continuity: {str(e)}")
            self.preencher_table_log()


    def adicionar_planner(self):
        # CORRIGI
        name = ui.new_planner.text().strip()
        alias = ui.new_alias_planner.text().strip().upper()
        email = ui.new_planner_email.text().strip()
        registered_by = getpass.getuser()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not name or not alias or not email:
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
                    QMessageBox.information(None, "Planner Updated", f"Planner '{alias}' updated successfully.")
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
            QMessageBox.information(None, "Planner Added", f"Planner '{alias}' added successfully.")
            ui.new_planner.clear()
            ui.new_alias_planner.clear()
            ui.new_planner_email.clear()
            self.preencher_table_log()

        except Exception as e:
            log_event(f"[ERROR] Failed to add/edit planner: {str(e)}")
            self.preencher_table_log()


    def adicionar_sourcing(self):
        name = ui.new_sourcing.text().strip()
        alias = ui.new_alias_sourcing.text().strip().upper()
        email = ui.new_sourcing_email.text().strip()
        registered_by = getpass.getuser()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not name or not alias or not email:
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
                    QMessageBox.information(None, "Sourcing Updated", f"Sourcing '{alias}' updated successfully.")
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
            QMessageBox.information(None, "Sourcing Added", f"Sourcing '{alias}' added successfully.")
            ui.new_sourcing.clear()
            ui.new_alias_sourcing.clear()
            ui.new_sourcing_email.clear()
            self.preencher_table_log()

        except Exception as e:
            log_event(f"[ERROR] Failed to add/edit sourcing: {str(e)}")
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
                QMessageBox.warning(None, "Already Exists", f"The Business Unit '{bu}' already exists.")
                return

            create(
                "INSERT INTO business_unit_table (bu, register_date, registered_by) VALUES (?, ?, ?)",
                (bu, now, registered_by),
                log_description=f"Added new Business Unit '{bu}' by {registered_by}"
            )

            self.carregar_todos_bus()
            QMessageBox.information(None, "Success", f"Business Unit '{bu}' added successfully.")
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
            return  
        try:
            resultado = read("SELECT categories_id FROM categories_table WHERE category = ?", (category,))
            if resultado:
                QMessageBox.warning(None, "Already Exists", f"The category '{category}' already exists.")
                return

            create(
                "INSERT INTO categories_table (category, register_date, registered_by) VALUES (?, ?, ?)",
                (category, now, registered_by),
                log_description=f"Added new category '{category}' by {registered_by}"
            )

            self.carregar_todos_categories()
            QMessageBox.information(None, "Success", f"Category '{category}' added successfully.")
            ui.new_category_2.clear()
            self.preencher_table_log()

        except Exception as e:
            log_event(f"[ERROR] Failed to add category: {str(e)}")
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

            QMessageBox.information(janela_principal, "Success", "Criteria updated")
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
        pass

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
                QMessageBox.warning(None, "Warning", "The 'Vendor' field cannot be empty.")
                return

            # Verifica se o fornecedor existe
            resultado = read("SELECT * FROM supplier_database_table WHERE supplier_id = ?", (supplier_id,))
            if not resultado:
                QMessageBox.information(None, "Information", f"The vendor '{vendor_name}' was not found in the database.")
                return

            # Atualiza dados na tabela
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

            QMessageBox.information(None, "Success", f"Supplier data for '{vendor_name}' was successfully updated.")

        except Exception as e:
            QMessageBox.critical(None, "Error", f"An error occurred while updating supplier:\n{str(e)}")
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
            QMessageBox.warning(None, "Warning", "No row selected.")
            return

        item_id = tabela.item(linha, 0)
        if not item_id:
            QMessageBox.warning(None, "Warning", "Record ID not found.")
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
            QMessageBox.critical(None, "Error", f"Failed to delete record:\n{e}")
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
        #preencher tambem campo emails
      

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


    def verificar_riscos(self):
        meta = ui.target_criteria.value()

        query_base = """
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
            GROUP BY s.supplier_id, s.supplier_name, sl.bu
            HAVING media_score {op} ?
        """

        query_riscos = query_base.format(op='<')
        query_ok = query_base.format(op='>=')

        riscos = read(query_riscos, (meta,))
        ok = read(query_ok, (meta,))  

        headers = ["ID", "Supplier", "BU", "Q1", "Q2", "Q3", "Q4", "Average Score"]
        table_risks = ui.table_risks

        def preencher_tabela(tabela, dados):
            tabela.clearContents()
            tabela.setRowCount(len(dados))
            tabela.setColumnCount(len(headers))
            tabela.setHorizontalHeaderLabels(headers)

            for i, (id_, fornecedor, bu, q1, q2, q3, q4, media) in enumerate(dados):
                row_items = [
                    QTableWidgetItem(str(id_)),
                    QTableWidgetItem(str(fornecedor)),
                    QTableWidgetItem(str(bu)),
                    QTableWidgetItem(f"{q1:.1f}" if q1 is not None else "-"),
                    QTableWidgetItem(f"{q2:.1f}" if q2 is not None else "-"),
                    QTableWidgetItem(f"{q3:.1f}" if q3 is not None else "-"),
                    QTableWidgetItem(f"{q4:.1f}" if q4 is not None else "-"),
                    QTableWidgetItem(f"{media:.1f}")
                ]

                for j, item in enumerate(row_items):
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    item.setFlags(QtCore.Qt.ItemIsEnabled)
                    tabela.setItem(i, j, item)

            tabela.setColumnWidth(0, 30)   # ID
            tabela.setColumnWidth(2, 70)   # BU
            tabela.setColumnWidth(3, 50)   # Q1
            tabela.setColumnWidth(4, 50)   # Q2
            tabela.setColumnWidth(5, 50)   # Q3
            tabela.setColumnWidth(6, 50)   # Q4
            tabela.setColumnWidth(7, 100)  # Média

            tabela.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)  # Supplier

        preencher_tabela(table_risks, riscos)

        ui.total_risks.setText(str(len(riscos)))
        ui.total_geral2.setText(f"/{len(riscos) + len(ok)}")


    def comparar_senha_edicao_criteria(self) -> bool:
        # Não crie tabela aqui, isso deve ser feito em setup do DB!

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
                QMessageBox.warning(dialog, "Input Error", "Please enter a password.")
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
                QMessageBox.warning(dialog, "Access Denied", "Incorrect password.")

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
            import os, json
            from pathlib import Path

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
            import os, json
            from pathlib import Path

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
ui.btn_register_new_supplier.clicked.connect(lambda: Functions.registrar_novo_usuario())
ui.btn_update_criteria.clicked.connect(lambda: funcoes.atualizar_criterios_no_banco())
ui.btn_vendor_score.clicked.connect(lambda: funcoes.abrir_janela_select_supplier("score"))
ui.btn_vendor_timeline.clicked.connect(lambda: funcoes.abrir_janela_select_supplier("timeline"))
ui.btn_vendor_register.clicked.connect(lambda: funcoes.abrir_janela_select_supplier("update"))
ui_login.btn_login.clicked.connect(lambda: funcoes.iniciar_splash())


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