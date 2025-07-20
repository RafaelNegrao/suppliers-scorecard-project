import sys
import random
import plotly.graph_objects as go
import sqlite3
import plotly.io as pio
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QLabel,QMessageBox,QTableWidgetItem
from PyQt5.QtCore import Qt, QEventLoop, QTimer
from PyQt5.QtGui import QIcon
from Interface import Ui_MainWindow
from loginWindow import Ui_LoginWindow
from PyQt5.QtWidgets import QHeaderView,QVBoxLayout,QMessageBox,QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox
from PyQt5 import QtWidgets, QtWebEngineWidgets, QtCore
from register import Ui_registerWindow
from selectSupplier import Ui_windowSelectSupplier
from crud import create_table, read, create,update,delete,read_custom
from PyQt5.QtCore import QEventLoop, QTimer, Qt
from PyQt5.QtGui import QPixmap





class Functions(QtCore.QObject):
    def __init__(self, ui_login, janela_login,janela_register ,janela_principal, ui_main, janela_select,parent=None):
        super().__init__(parent)
        self.ui_login = ui_login
        self.janela_login = janela_login
        self.janela_principal = janela_principal
        self.ui_main = ui_main 
        self.ui_select = janela_select
        self.ui_register = janela_register
       
        
        tab_widget = self.ui_main.tabWidget  

        for i in range(tab_widget.count()):
            tab_widget.setTabIcon(i, QIcon())

        tab_widget = self.ui_main.tabWidget  

        tab_widget.tabBar().hide()

    from PyQt5.QtWidgets import QMessageBox


    def salvar_novo_supplier(self, _=None):
        vendor = ui_register.vendor_register_new.text().strip().upper()
        supplier = ui_register.supplier_register.text().strip().upper()
        bu = ui_register.bu_register_new.currentText().strip()
        category = ui_register.new_category.currentText().strip()
        sqie = ui_register.sqie_register_new.currentText().strip()
        sourcing = ui_register.sourcing_register_new.currentText().strip()
        continuity = ui_register.continuity_register_new.currentText().strip()
        ssid = ui_register.ssid_register_new.text().strip().upper()
        country = ui_register.country_register_new.text().strip().upper()
        region = ui_register.region_register_new.text().strip().upper()
        document = ui_register.document_register_new.text().strip().upper()

        campos_obrigatorios = {
            "Vendor": vendor,
            "Supplier": supplier,
            "BU": bu,
            "Category": category,
            "SQIE": sqie,
            "Sourcing": sourcing,
            "Continuity": continuity,
            "SSID": ssid,
            "Country": country,
            "Region": region,
            "Document": document
        }

        for nome_campo, valor in campos_obrigatorios.items():
            if not valor:
                QMessageBox.warning(None, "Required Field", f"The field '{nome_campo}' is required.")
                return

        try:
            # Usando o CRUD genérico
            create("supplier_list", {
                "vendor": vendor,
                "Supplier": supplier,
                "BU": bu,
                "category": category,
                "sqie": sqie,
                "sourcing": sourcing,
                "continuity": continuity,
                "ssid": ssid,
                "country": country,
                "region": region,
                "document": document
            })

            QMessageBox.information(None, "Success", "Supplier saved successfully.")

            # Zera os campos
            ui_register.vendor_register_new.setText("")
            ui_register.supplier_register.setText("")
            ui_register.bu_register_new.setCurrentIndex(0)
            ui_register.new_category.setCurrentIndex(0)
            ui_register.sqie_register_new.setCurrentIndex(0)
            ui_register.sourcing_register_new.setCurrentIndex(0)
            ui_register.continuity_register_new.setCurrentIndex(0)
            ui_register.ssid_register_new.setText("")
            ui_register.country_register_new.setText("")
            ui_register.region_register_new.setText("")
            ui_register.document_register_new.setText("")

            # Fecha a janela de cadastro
            janela_register.close()

            # Atualiza vendor_register
            fornecedores = self.carregar_fornecedores_do_banco()
            ui.vendor_register.blockSignals(True)
            ui.vendor_register.clear()
            #ui.vendor_register.addItems(fornecedores)
            ui.vendor_register.blockSignals(False)

        except Exception as erro:
            QMessageBox.critical(None, "Error", f"Error while saving supplier:\n{erro}")


    def iniciar_splash(self):
        self.janela_login.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.messages = [
            "Initializing user interface...",
            "Loading configuration files...",
            "Importing required Python modules...",
            "Checking system environment...",
            "Verifying user permissions...",
            "Establishing database connection...",
            "Initializing session context...",
            "Syncing Sqlite3...",
            "Finalizing setup...",
            "All up to date",
            "Startup complete."
        ]
        
        self.msg_index = 0
        self.total = len(self.messages)

        def mostrar_proxima_mensagem():
            if self.msg_index < self.total:
          
                progresso = int((self.msg_index + 1) * (100 / self.total))
                self.ui_login.barra_progresso.setValue(progresso)

                mensagens_atuais = self.ui_login.campoStats.toPlainText()
                nova_mensagem = self.messages[self.msg_index]
                self.ui_login.campoStats.setPlainText(mensagens_atuais + nova_mensagem + "\n")
                self.msg_index += 1

                delay = random.randint(5, 800)
                QtCore.QTimer.singleShot(delay, mostrar_proxima_mensagem)
            else:
                self.janela_login.close()
                self.janela_principal.show()
                self.carregar_graficos() 

        mostrar_proxima_mensagem()


    def atualizar_media_12_meses(self):
        id = ui.id_timeline.text().strip()
        if not id:
            ui.average_12month.setText("")
            return

        registros = read("suppliers_timeline", {"id": id})
        if not registros:
            ui.average_12month.setText("")
            return

        try:
            # usa os índices corretos: ano = 4, mes = 3
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
                score = float(row[9])  # total_score
                dados[(ano, mes)] = score
            except:
                pass

        valores = [dados.get((ano, mes), 0) for ano, mes in ultimos_12_meses]
        divisor = len([v for v in valores if v > 0]) or 1
        media_12_meses = sum(valores) / divisor

        ui.average_12month.setText(f" {int(media_12_meses)}")
        

    def atualizar_media_geral(self):
        id = ui.id_timeline.text().strip()
        if not id:
            ui.overhall_average.setText("")
            return

        registros = read("suppliers_timeline", {"id": id})
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


    def atualizar_media_6_meses(self):
        id = ui.id_timeline.text().strip()
        if not id:
            ui.average_6month.setText("")
            return

        registros = read("suppliers_timeline", {"id": id})
        if not registros:
            ui.average_6month.setText("")
            return

        try:
            # Ordena para pegar o registro mais recente (ano=4, mes=3)
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
                score = float(row[9])  # total_score
                dados[(ano, mes)] = score
            except:
                pass

        valores = [dados.get((ano, mes), 0) for ano, mes in ultimos_6_meses]
        divisor = len([v for v in valores if v > 0]) or 1
        media_6_meses = sum(valores) / divisor

        ui.average_6month.setText(f" {int(media_6_meses)}")


    def atualizar_media_3_meses(self):
        id = ui.id_timeline.text().strip()
        if not id:
            ui.average_3month.setText("")
            return

        registros = read("suppliers_timeline", {"id": id})
        if not registros:
            ui.average_3month.setText("")
            return

        try:
            # Ordena por ano (índice 4) e mês (índice 3) decrescente para pegar o último registro
            ordenado = sorted(registros, key=lambda r: (int(r[4]), int(r[3])), reverse=True)
            max_ano, max_mes = int(ordenado[0][4]), int(ordenado[0][3])
        except Exception as e:
            print(f"Erro ao identificar último ano/mês: {e}")
            ui.average_3month.setText("")
            return

        data_base = QtCore.QDate(max_ano, max_mes, 1)
        ultimos_3_meses = [(data_base.addMonths(-i).year(), data_base.addMonths(-i).month()) for i in range(2, -1, -1)]

        dados = {}
        for row in registros:
            try:
                ano = int(row[4])
                mes = int(row[3])
                score = float(row[9])  # total_score
                dados[(ano, mes)] = score
            except:
                pass

        valores = [dados.get((ano, mes), 0) for ano, mes in ultimos_3_meses]
        divisor = len([v for v in valores if v > 0]) or 1
        media_3_meses = sum(valores) / divisor

        ui.average_3month.setText(f" {int(media_3_meses)}")


    def total_score_possivel(self):
        total = (int(ui.quality_packege_criteria.value())*10) + \
                (int(ui.nil_criteria.value())*10) + \
                (int(ui.otif_criteria.value())*10) + \
                (int(ui.quality_pickup_criteria.value())*10)
        
        total_str = f" /{total}"
        
        # if ui.overhall_average.text():
        #     ui.total1.setText(total_str)
        # else:
        #     ui.total1.setText('')

        # if ui.average_12month.text():
        #     ui.total2.setText(total_str)
        # else:
        #     ui.total2.setText('')

        # if ui.average_6month.text():
        #     ui.total3.setText(total_str)
        # else:
        #     ui.total3.setText('')

        # if ui.average_3month.text():
        #     ui.total4.setText(total_str)
        # else:
        #     ui.total4.setText('')


    def criar_grafico_coluna(self, container_widget):
        id = self.ui_main.id_timeline.text().strip()
        if not id:
            return

        rows = read("suppliers_timeline", {"id": id})

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

        # Cores simples: verde se >= meta, vermelho se < meta
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

            /* Garante que o cursor mude quando o usuário passar o mouse sobre as barras */
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
        id_fornecedor = self.ui_main.id_timeline.text().strip()
        if not id_fornecedor:
            return

        rows = read("suppliers_timeline", {"id": id_fornecedor})
        if not rows:
            self.ui_main.tableDetails.clearContents()
            self.ui_main.tableDetails.setRowCount(0)
            return

        tabela = self.ui_main.tableDetails
        tabela.clearContents()
        tabela.setRowCount(len(rows))
        tabela.setColumnCount(9)
        tabela.setHorizontalHeaderLabels([
            "ID", "Year", "Month", "Quality Package", "Quality Pick Up", "NIL", "OTIF", "Total Score", "Comments"
        ])

        for i, row in enumerate(rows):
            # row = (row_id, id, fornecedor, mes, ano, quality_package, quality_pickup, nil, otif, total_score, comment)
            row_id = row[0]
            ano = row[4]
            mes = row[3]
            q_package = row[5]
            q_pickup = row[6]
            nil = row[7]
            otif = row[8]
            total = row[9]
            comment = row[10]

            data_str = f"{ano}/{int(mes):02}"
            valores = [row_id, ano, mes, q_package, q_pickup, nil, otif, total, comment]

            for j, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignCenter)
                tabela.setItem(i, j, item)

        header = tabela.horizontalHeader()
        header.setSectionResizeMode(8, QHeaderView.Stretch)
        tabela.resizeColumnsToContents()
        tabela.resizeRowsToContents()


    def registrar_novo_usuario():
        try:
            # Categorias
            categorias = [row[0] for row in read_custom("SELECT category FROM categories ORDER BY category ASC")]

            # Business Units
            business_units = [row[0] for row in read_custom("SELECT bu FROM business_units ORDER BY bu ASC")]

            # SQIE
            sqies = [row[0] for row in read_custom("SELECT nome FROM sqie ORDER BY nome ASC")]

            # Sourcing
            sourcings = [row[0] for row in read_custom("SELECT nome FROM sourcing ORDER BY nome ASC")]

            # Continuity
            continuities = [row[0] for row in read_custom("SELECT nome FROM continuity ORDER BY nome ASC")]

            # Preencher os ComboBoxes
            ui_register.new_category.clear()
            ui_register.new_category.addItem("")
            ui_register.new_category.addItems(categorias)

            ui_register.bu_register_new.clear()
            ui_register.bu_register_new.addItem("")
            ui_register.bu_register_new.addItems(business_units)

            ui_register.sqie_register_new.clear()
            ui_register.sqie_register_new.addItem("")
            ui_register.sqie_register_new.addItems(sqies)

            ui_register.sourcing_register_new.clear()
            ui_register.sourcing_register_new.addItem("")
            ui_register.sourcing_register_new.addItems(sourcings)

            ui_register.continuity_register_new.clear()
            ui_register.continuity_register_new.addItem("")
            ui_register.continuity_register_new.addItems(continuities)

        except Exception as e:
            print(f"Error loading data: {e}")

        janela_register.show()



    def carregar_graficos(self):
        self.criar_grafico_coluna(self.ui_main.lineChart)
        self.atualizar_media_12_meses()
        self.atualizar_media_6_meses()
        self.atualizar_media_3_meses()
        self.atualizar_media_geral()
        self.preencher_tabela_resultados()
        self.total_score_possivel()
        

    def mudar_pagina(indice):
        ui.tabWidget.setCurrentIndex(indice)

        buttons = [
            ui.btn_home,
            ui.btn_score,
            ui.btn_timeline,
            ui.btn_send_mail,
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
                        color: black;
                    }}
                    QPushButton#{btn.objectName()}:hover {{
                        background-color: rgba(180, 180, 180, 255);
                        border-top-right-radius: 15px; border-bottom-right-radius: 15px;
                    }}
                """
                btn.setStyleSheet(style)

        # Depois anima o botão selecionado
        selected_btn = buttons[indice]
        for step in range(steps + 1):
            border_width = (max_border / steps) * step
            style = f"""
                QPushButton#{selected_btn.objectName()} {{
                    background-color: rgba(200, 200, 200, 255);
                    border: none;
                    border-left: {border_width:.2f}px solid rgba(200, 0, 0, 255);
                    border-top-right-radius: 15px; border-bottom-right-radius: 15px;
                    text-align: left;
                    padding: 10px;
                }}
                QPushButton#{selected_btn.objectName()}:hover {{
                    background-color: rgba(180, 180, 180, 255);
                    border-top-right-radius: 15px; border-bottom-right-radius: 15px;
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

        ui.total_score.setText(str(total_score))


    def salvar_score(self):
        try:
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

            if not id_fornecedor or fornecedor == "" or mes == "" or ano == "":
                QMessageBox.warning(janela_principal, "Error", "ID, supplier, month and year are required to save the score")
                return

            # Cria a tabela se necessário
            create_table("suppliers_timeline", {
                "row_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "id": "INTEGER NOT NULL",
                "fornecedor": "TEXT NOT NULL",
                "mes": "TEXT NOT NULL",
                "ano": "TEXT NOT NULL",
                "quality_package": "INTEGER NOT NULL",
                "quality_pickup": "INTEGER NOT NULL",
                "nil": "INTEGER NOT NULL",
                "otif": "INTEGER NOT NULL",
                "total_score": "TEXT NOT NULL",
                "comment": "TEXT",
                "UNIQUE(id, mes, ano)": ""  # Define a constraint UNIQUE
            })

            dados = {
                "id": id_fornecedor,
                "fornecedor": fornecedor,
                "mes": mes,
                "ano": ano,
                "quality_package": pacote,
                "quality_pickup": retirada,
                "nil": nil,
                "otif": otif,
                "total_score": total,
                "comment": comment
            }

            try:
                create("suppliers_timeline", dados)
                QMessageBox.information(janela_principal, "Success", "Data saved successfully")
            except sqlite3.IntegrityError:
                resposta = QMessageBox.question(
                    janela_principal,
                    "Score already exists",
                    "This supplier already has a score registered for this month and year.\nDo you want to overwrite it?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if resposta == QMessageBox.Yes:
                    update("suppliers_timeline",
                        {
                            "quality_package": pacote,
                            "quality_pickup": retirada,
                            "nil": nil,
                            "otif": otif,
                            "total_score": total,
                            "comment": comment
                        },
                        {"id": id_fornecedor, "mes": mes, "ano": ano}
                    )
                    QMessageBox.information(janela_principal, "Success", "Data updated successfully")
                else:
                    return

            # Limpa os campos após salvar ou atualizar
            ui.id_query.setText("")
            ui.vendor_select.setText("")
            ui.month.setCurrentIndex(0)
            ui.year.setCurrentIndex(0)
            ui.quality_package_input.setValue(0)
            ui.quality_pickup_input.setValue(0)
            ui.nil_input.setValue(0)
            ui.otif_input.setValue(0)
            ui.total_score.setText(str(0))
            ui.comments.clear()
            ui.supplier_query.setText("")
            ui.bu_query.setText("")
            ui.continuity_query.setText("")
            ui.sqie_query.setText("")
            ui.sourcing_query.setText("")
            ui.category_query.setText("")
            ui.ssid_query.setText("")
            ui.country_query.setText("")
            ui.region_query.setText("")
            ui.document_query.setText("")

        except Exception as e:
            QMessageBox.critical(janela_principal, "Error", f"An error occurred while saving:\n{str(e)}")


    def carregar_fornecedores_do_banco(self):
        try:
            # Utiliza a função read para buscar os dados da tabela 'supplier_list'
            resultados = read("supplier_list")

            # Extrai a coluna 'vendor' assumindo que ela está na primeira posição
            fornecedores = [str(linha[0]) for linha in sorted(resultados, key=lambda x: x[0])]
            fornecedores.insert(0, "")

            return fornecedores
        except Exception as erro:
            print(f"[ERRO - carregar_fornecedores_do_banco] {erro}")
            return [""]


    def apagar_todos_campos_register(self):
        ui.vendor_register.blockSignals(True)
        ui.vendor_register.setText("")
        ui.vendor_register.blockSignals(False)

        ui.new_category.setCurrentText("")
        ui.bu_register.setCurrentText("")
        ui.supplier_register.setText("")
        ui.sqie_register.setCurrentText("")
        ui.sourcing_register.setCurrentText("")
        ui.continuity_register.setCurrentText("")
        ui.ssid_register.setText("")           
        ui.country_register.setText("")        
        ui.region_register.setText("")       
        ui.document_register.setText("") 
    

    def adicionar_sqie(self):
        dialog = QDialog()
        dialog.setWindowTitle("Add New SQIE")
        dialog.setFixedWidth(400)

        layout = QVBoxLayout(dialog)

        label = QLabel("Enter the name of the new SQIE:")
        campo = QLineEdit()
        campo.setPlaceholderText("SQIE name")
        campo.setMinimumWidth(350)

        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(dialog.accept)
        botoes.rejected.connect(dialog.reject)

        layout.addWidget(label)
        layout.addWidget(campo)
        layout.addWidget(botoes)

        if dialog.exec() == QDialog.Accepted:
            new_sqie = campo.text().strip()
            if not new_sqie:
                QMessageBox.warning(None, "Required Field", "The SQIE name cannot be empty.")
                return

            try:
                create("sqie", {"nome": new_sqie})
                self.carregar_todos_sqie()
                QMessageBox.information(None, "Success", f"SQIE '{new_sqie}' added successfully.")
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to add SQIE:\n{str(e)}")


    def adicionar_continuity(self):
        dialog = QDialog()
        dialog.setWindowTitle("Add New Continuity")
        dialog.setFixedWidth(400)

        layout = QVBoxLayout(dialog)

        label = QLabel("Enter the name of the new Continuity:")
        campo = QLineEdit()
        campo.setPlaceholderText("Continuity name")
        campo.setMinimumWidth(350)

        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(dialog.accept)
        botoes.rejected.connect(dialog.reject)

        layout.addWidget(label)
        layout.addWidget(campo)
        layout.addWidget(botoes)

        if dialog.exec() == QDialog.Accepted:
            new_continuity = campo.text().strip()
            if not new_continuity:
                QMessageBox.warning(None, "Required Field", "The Continuity name cannot be empty.")
                return

            try:
                create("continuity", {"nome": new_continuity})
                self.carregar_todos_continuity()
                QMessageBox.information(None, "Success", f"Continuity '{new_continuity}' added successfully.")
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to add Continuity:\n{str(e)}")


    def adicionar_sourcing(self):
        dialog = QDialog()
        dialog.setWindowTitle("Add New Sourcing")
        dialog.setFixedWidth(400)

        layout = QVBoxLayout(dialog)

        label = QLabel("Enter the name of the new Sourcing:")
        campo = QLineEdit()
        campo.setPlaceholderText("Sourcing name")
        campo.setMinimumWidth(350)

        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(dialog.accept)
        botoes.rejected.connect(dialog.reject)

        layout.addWidget(label)
        layout.addWidget(campo)
        layout.addWidget(botoes)

        if dialog.exec() == QDialog.Accepted:
            new_sourcing = campo.text().strip()
            if not new_sourcing:
                QMessageBox.warning(None, "Required Field", "The Sourcing name cannot be empty.")
                return

            try:
                create("sourcing", {"nome": new_sourcing})
                self.carregar_todos_sourcing()
                QMessageBox.information(None, "Success", f"Sourcing '{new_sourcing}' added successfully.")
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to add Sourcing:\n{str(e)}")


    def adicionar_bu(self):
        dialog = QDialog()
        dialog.setWindowTitle("Add New Business Unit")
        dialog.setFixedWidth(400)

        layout = QVBoxLayout(dialog)

        label = QLabel("Enter the name of the new Business Unit:")
        campo = QLineEdit()
        campo.setPlaceholderText("Business Unit name")
        campo.setMinimumWidth(350)

        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(dialog.accept)
        botoes.rejected.connect(dialog.reject)

        layout.addWidget(label)
        layout.addWidget(campo)
        layout.addWidget(botoes)

        if dialog.exec() == QDialog.Accepted:
            new_bu = campo.text().strip()
            if not new_bu:
                QMessageBox.warning(None, "Required Field", "The Business Unit name cannot be empty.")
                return

            try:
                create("business_units", {"bu": new_bu})
                self.carregar_todos_bus()
                QMessageBox.information(None, "Success", f"Business Unit '{new_bu}' added successfully.")
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to add Business Unit:\n{str(e)}")


    def adicionar_category(self):
        dialog = QDialog()
        dialog.setWindowTitle("Add New Category")
        dialog.setFixedWidth(400)

        layout = QVBoxLayout(dialog)

        label = QLabel("Enter the name of the new category:")
        campo = QLineEdit()
        campo.setPlaceholderText("Category name")
        campo.setMinimumWidth(350)

        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(dialog.accept)
        botoes.rejected.connect(dialog.reject)

        layout.addWidget(label)
        layout.addWidget(campo)
        layout.addWidget(botoes)

        if dialog.exec() == QDialog.Accepted:
            new_category = campo.text().strip()
            if not new_category:
                QMessageBox.warning(None, "Required Field", "Category name cannot be empty.")
                return

            try:
                create("categories", {"category": new_category})
                self.carregar_todos_categories()
                QMessageBox.information(None, "Success", f"Category '{new_category}' added successfully.")
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to add category:\n{str(e)}")


    def carregar_criterios_dos_campos(self):
        campos = {
            "Quality-Supplier Package": self.ui_main.quality_packege_criteria,
            "Quality of Pick Up": self.ui_main.quality_pickup_criteria,
            "NIL-CBL": self.ui_main.nil_criteria,
            "OTIF-NIL": self.ui_main.otif_criteria,
            "Target": self.ui_main.target_criteria
        }

        try:
            for criterio_nome, spinbox in campos.items():
                resultados = read("criteria", {"category": criterio_nome})
                
                if resultados:
                    linha = resultados[0]
                    try:
                        valor_str = linha[2]  # Third column assumed to be 'value'
                        valor = int(float(valor_str))
                        spinbox.setValue(valor)
                    except Exception as conv_erro:
                        print(f"[Error] Failed to convert value for '{criterio_nome}': '{linha}' → {conv_erro}")
                else:
                    print(f"[Warning] No data found for '{criterio_nome}'")
        except Exception as e:
            print(f"[Critical Error] Failed to load criteria: {e}")


    def atualizar_criterios_no_banco(self):
        try:
            campos = {
                "Quality-Supplier Package": self.ui_main.quality_packege_criteria.value(),
                "Quality of Pick Up": self.ui_main.quality_pickup_criteria.value(),
                "NIL-CBL": self.ui_main.nil_criteria.value(),
                "OTIF-NIL": self.ui_main.otif_criteria.value(),
                "Target": self.ui_main.target_criteria.value()
            }

            for categoria, valor in campos.items():
                update("criteria", {"value": valor}, {"category": categoria})

            # Bloqueia os campos após salvar
            ui.quality_packege_criteria.setEnabled(False)
            ui.quality_pickup_criteria.setEnabled(False)
            ui.nil_criteria.setEnabled(False)
            ui.otif_criteria.setEnabled(False)
            ui.target_criteria.setEnabled(False)
            ui.btn_unlock_criteria_edit.setText("🔒")

            QMessageBox.information(janela_principal, "Success", "Criteria updated")
        except Exception as e:
            print(f"Erro ao atualizar critérios: {e}")


    def carregar_todos_categories(self):
        try:
            resultados = read("categories")

            categorias = sorted(set(row[1] for row in resultados))  # row[1] assume que category é a 2ª coluna

            ui.new_category.clear()
            ui.new_category.addItem("")
            for categoria in categorias:
                ui.new_category.addItem(categoria)

        except Exception as e:
            print(f"Erro ao carregar categories: {e}")


    def carregar_todos_bus(self):
        try:
            resultados = read("business_units")

            # Supondo que a coluna 'bu' é a segunda (índice 1)
            bus = sorted(set(row[1] for row in resultados))

            ui.bu_register.clear()
            ui.bu_register.addItem("")
            for b in bus:
                ui.bu_register.addItem(b)

        except Exception as e:
            print(f"Erro ao carregar business units: {e}")


    def carregar_todos_continuity(self):
        try:
            resultados = read("continuity")
            nomes = sorted(row[1] for row in resultados)  # Assumindo que 'nome' é a 2ª coluna (índice 1)

            self.ui_main.continuity_register.clear()
            self.ui_main.continuity_register.addItem("")
            self.ui_main.continuity_register.addItems(nomes)

        except Exception as e:
            print(f"Erro ao carregar continuity: {e}")


    def carregar_todos_sourcing(self):
        try:
            resultados = read("sourcing")
            nomes = sorted(row[1] for row in resultados)

            self.ui_main.sourcing_register.clear()
            self.ui_main.sourcing_register.addItem("")
            self.ui_main.sourcing_register.addItems(nomes)

        except Exception as e:
            print(f"Erro ao carregar sourcing: {e}")


    def carregar_todos_sqie(self):
        try:
            resultados = read("sqie")
            nomes = sorted(row[1] for row in resultados)

            self.ui_main.sqie_register.clear()
            self.ui_main.sqie_register.addItem("")
            self.ui_main.sqie_register.addItems(nomes)

        except Exception as e:
            print(f"Erro ao carregar sqie: {e}")


    def atualizar_dados_supplier(self):
        try:
            # Get data from UI
            id = ui.id_register.text()
            vendor = ui.vendor_register.text().strip().upper()
            supplier = ui.supplier_register.text().strip().upper()
            category = ui.new_category.currentText().strip()
            bu = ui.bu_register.currentText().strip()
            sqie = ui.sqie_register.currentText().strip()
            sourcing = ui.sourcing_register.currentText().strip()
            continuity = ui.continuity_register.currentText().strip()
            ssid = ui.ssid_register.text().strip()
            country = ui.country_register.text().strip().upper()
            region = ui.region_register.text().strip().upper()
            document = ui.document_register.text().strip().upper()

            if not vendor:
                QMessageBox.warning(None, "Warning", "The 'Vendor' field cannot be empty.")
                return

            resultado = read("supplier_list", {"id": id})
            if not resultado:
                QMessageBox.information(None, "Information", f"The vendor '{vendor}' was not found in the database.")
                return

            # Atualiza supplier_list
            update("supplier_list", {
                "vendor": vendor,
                "Supplier": supplier,
                "BU": bu,
                "category": category,
                "sqie": sqie,
                "sourcing": sourcing,
                "continuity": continuity,
                "ssid": ssid,
                "country": country,
                "region": region,
                "document": document
            }, {"id": id})

            # Atualiza suppliers_timeline com o novo nome do fornecedor (vendor)
            update("suppliers_timeline", {"fornecedor": vendor}, {"id": id})

            QMessageBox.information(None, "Success", f"Supplier data for '{vendor}' was successfully updated.")

        except Exception as e:
            QMessageBox.critical(None, "Error", f"An error occurred while updating supplier:\n{str(e)}")

    def ajustar_colunas_tabela_new_contact(self):
        
        ui.table_new_contact.setColumnWidth(0, 50)
        header = ui.table_new_contact.horizontalHeader()
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)



    def abrir_janela_select_supplier(self, origem):
        self.origem_botao_chamador = origem
        try:
            # Abre a janela de seleção
            janela_select.show()

            resultados = read("supplier_list")

            # Limpa e configura a tabela
            ui_select.table_select_supplier.setRowCount(0)
            ui_select.table_select_supplier.setColumnCount(4)
            ui_select.table_select_supplier.setHorizontalHeaderLabels(["ID", "Vendor", "Supplier", "BU"])
            ui_select.table_select_supplier.setColumnWidth(0, 50)
            ui_select.table_select_supplier.setColumnWidth(1, 400)
            ui_select.table_select_supplier.setColumnWidth(2, 150)
            ui_select.table_select_supplier.setColumnWidth(3, 60)

            for row_idx, row in enumerate(sorted(resultados, key=lambda x: x[1])):  # Ordena por vendor (índice 1)
                ui_select.table_select_supplier.insertRow(row_idx)
                for col_idx in range(4):
                    item = QTableWidgetItem(str(row[col_idx]))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    ui_select.table_select_supplier.setItem(row_idx, col_idx, item)

        except Exception as e:
            print(f"Error loading suppliers: {e}")


    def evento_ao_abrir(self):
        self.carregar_todos_sqie()
        self.carregar_todos_continuity()
        self.carregar_todos_sourcing()
        self.carregar_todos_categories()
        self.carregar_todos_bus()
        self.carregar_criterios_dos_campos()
        self.ajustar_colunas_tabela_new_contact()


    def evento_ao_fechar(self, event):
        janela_register.close()
        janela_select.close()
        
        event.accept()


    def mostrar_info(self, checked=False):
    
        QMessageBox.information(
            None,
            "Information",
            "Developed by Rafael Negrão de Souza - Supply Continuity Intern\n"
            "rafael.negrao.souza@cummins.com"
        )


    def apagar_registro_selecionado(self):
        tabela = self.ui_main.tableDetails
        linha = tabela.currentRow()

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
            delete("suppliers_timeline", {"row_id": id_registro})

            QMessageBox.information(None, "Success", "Record successfully deleted.")
            self.preencher_tabela_resultados()
            self.carregar_graficos()

            # Ajustar a última coluna para preencher o espaço restante
            self.ui_main.tableDetails.horizontalHeader().setSectionResizeMode(
                self.ui_main.tableDetails.columnCount() - 1, QtWidgets.QHeaderView.Stretch
            )

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to delete record:\n{e}")


    def buscar_dados_supplier_por_id(self, id_fornecedor):
        try:
            resultados = read("supplier_list", {"id": id_fornecedor})
            return resultados[0] if resultados else None
        except Exception as e:
            print(f"Error fetching supplier data by ID: {e}")
            return None
        
    
    def selecionar_vendor_pelo_botao(self):
        linha = ui_select.table_select_supplier.currentRow()
        if linha < 0:
            print("Nenhuma linha selecionada.")
            return

        id_text = ui_select.table_select_supplier.item(linha, 0).text()
        if not id_text or not id_text.isdigit():
            print("ID inválido.")
            return

        id_fornecedor = int(id_text)
        #ui.id_query.setText(str(id_fornecedor))
        dados = self.buscar_dados_supplier_por_id(id_fornecedor)

        if not dados:
            print("Nenhum dado encontrado para o ID.")
            return

        # Ajuste o desempacotamento, incluindo id_ e corrigindo country
        (
            id_, vendor, supplier, bu, category, sqie,
            sourcing, continuity, ssid, country, region, document
        ) = dados

        if self.origem_botao_chamador == "score":
            self.preencher_score(id_text,vendor, supplier, bu, category, sqie, sourcing, continuity, ssid, country, region, document)
        elif self.origem_botao_chamador == "timeline":
            self.preencher_timeline(id_text, vendor, supplier, bu, category, sqie, sourcing, continuity)
        elif self.origem_botao_chamador == "register":
            self.preencher_register(id_text, vendor, supplier, bu, category, sqie, sourcing, continuity, ssid, country, region, document)

        janela_select.close()


    def apagar_todos_campos_query(self):
        ui.vendor_select.setText("")
        ui.category_query.setText("")
        ui.sqie_query.setText("")
        ui.sourcing_query.setText("")
        ui.continuity_query.setText("")
        ui.ssid_query.setText("")
        ui.country_query.setText("")
        ui.region_query.setText("")
        ui.document_query.setText("")
        ui.bu_query.setText("")
        ui.supplier_query.setText("")
        ui.id_query.setText("")


    def preencher_score(self,id, vendor, supplier, bu, category, sqie, sourcing, continuity,ssid,country,region,document):
        ui.id_query.setText(str(id))
        ui.vendor_select.setText(vendor)
        ui.category_query.setText(str(category) if category else "")
        ui.sqie_query.setText(str(sqie) if sqie else "")
        ui.sourcing_query.setText(str(sourcing) if sourcing else "")
        ui.continuity_query.setText(str(continuity) if continuity else "")
        ui.ssid_query.setText(str(ssid) if ssid else "")
        ui.country_query.setText(str(country) if country else "")
        ui.region_query.setText(str(region) if region else "")
        ui.document_query.setText(str(document) if document else "")
        ui.bu_query.setText(str(bu) if bu else "")
        ui.supplier_query.setText(str(supplier) if supplier else "")


    def preencher_timeline(self,id, vendor, supplier, bu, category, sqie, sourcing, continuity):
        ui.id_timeline.setText(id)
        ui.vendor_timeline.setText(vendor)
        ui.bu_query_2.setText(str(bu) if bu else "")
        ui.category_timeline.setText(str(category) if category else "")
        ui.sqie_timeline.setText(str(sqie) if sqie else "")
        ui.sourcing_timeline.setText(str(sourcing) if sourcing else "")
        ui.continuity_timeline.setText(str(continuity) if continuity else "")
        ui.supplier_timeline.setText(str(supplier) if supplier else "")
        self.carregar_graficos()


    def preencher_register(self,id, vendor, supplier, bu, category, sqie, sourcing, continuity,ssid,country,region,document):
        ui.id_register.setText(id)
        ui.vendor_register.setText(vendor)
        ui.bu_register.setCurrentText(str(bu) if bu else "")
        ui.new_category.setCurrentText(str(category) if category else "")
        ui.sqie_register.setCurrentText(str(sqie) if sqie else "")
        ui.sourcing_register.setCurrentText(str(sourcing) if sourcing else "")
        ui.continuity_register.setCurrentText(str(continuity) if continuity else "")
        ui.supplier_register.setText(str(supplier) if supplier else "")
        ui.ssid_register.setText(str(ssid) if ssid else "")
        ui.country_register.setText(str(country) if country else "")
        ui.region_register.setText(str(region) if region else "")
        ui.document_register.setText(str(document) if document else "")


    def verificar_riscos(self):
        meta = ui.target_criteria.value()

        query_base = """
            SELECT s.id, s.fornecedor, sl.BU, AVG(CAST(s.total_score AS FLOAT)) AS media_score
            FROM suppliers_timeline s
            JOIN supplier_list sl ON s.id = sl.id
            GROUP BY s.id, s.fornecedor, sl.BU
            HAVING media_score {op} ?
        """

        query_riscos = query_base.format(op='<')
        query_ok = query_base.format(op='>=')

        riscos = read_custom(query_riscos, (meta,))
        ok = read_custom(query_ok, (meta,))

        headers = ["ID", "Supplier", "BU", "Average Score"]
        table_risks = ui.tableWidget_risks
   

        def preencher_tabela(tabela, dados):
            tabela.clearContents()
            tabela.setRowCount(len(dados))
            tabela.setColumnCount(4)
            tabela.setHorizontalHeaderLabels(headers)

            for i, (id_, fornecedor, bu, media) in enumerate(dados):
                item_id = QTableWidgetItem(str(id_))
                item_supplier = QTableWidgetItem(str(fornecedor))
                item_bu = QTableWidgetItem(str(bu))
                item_score = QTableWidgetItem(str(int(media)))

                item_id.setTextAlignment(QtCore.Qt.AlignCenter)
                item_bu.setTextAlignment(QtCore.Qt.AlignCenter)
                item_score.setTextAlignment(QtCore.Qt.AlignCenter)

                for item in [item_id, item_supplier, item_bu, item_score]:
                    item.setFlags(QtCore.Qt.ItemIsEnabled)

                tabela.setItem(i, 0, item_id)
                tabela.setItem(i, 1, item_supplier)
                tabela.setItem(i, 2, item_bu)
                tabela.setItem(i, 3, item_score)

            tabela.setColumnWidth(0, 30)   # ID
            tabela.setColumnWidth(2, 80)   # BU
            tabela.setColumnWidth(3, 100)   # Score
            tabela.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        preencher_tabela(table_risks, riscos)

        # Totais
        riscos_count = len(riscos)
        ok_count = len(ok)
        total_geral = riscos_count + ok_count

        ui.total_risks.setText(str(riscos_count))
        ui.total_geral2.setText(f"/{total_geral}")


    def comparar_senha_edicao_criteria(self) -> bool:
        create_table("criteria_password_edit", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "password": "TEXT NOT NULL"
        })

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
            senha = campo.text()
            if read("criteria_password_edit", {"password": senha}):
                resultado["valido"] = True
                dialog.accept()

                # Habilita os campos diretamente
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


            
        







##########################################################################################################################################
##########################################################################################################################################
##########################################################################################################################################
##########################################################################################################################################


# ---- INICIALIZAÇÃO ----
app = QtWidgets.QApplication(sys.argv)

janela_principal = QtWidgets.QMainWindow()
janela_login = QtWidgets.QMainWindow()
janela_register = QtWidgets.QMainWindow()
janela_select = QtWidgets.QMainWindow()


ui = Ui_MainWindow()
ui.setupUi(janela_principal)

ui_login = Ui_LoginWindow()
ui_login.setupUi(janela_login)

ui_register = Ui_registerWindow()
ui_register.setupUi(janela_register)

ui_select = Ui_windowSelectSupplier()
ui_select.setupUi(janela_select)


funcoes = Functions(ui_login, janela_login,janela_register, janela_principal, ui,ui_select, janela_register)
funcoes.evento_ao_abrir()


janela_principal.closeEvent = funcoes.evento_ao_fechar


# Botões
ui.btn_home.clicked.connect(lambda: Functions.mudar_pagina(0))
ui.btn_score.clicked.connect(lambda: Functions.mudar_pagina(1))
ui.btn_timeline.clicked.connect(lambda: Functions.mudar_pagina(2))
ui.btn_send_mail.clicked.connect(lambda: Functions.mudar_pagina(3))
ui.btn_risks.clicked.connect(lambda: Functions.mudar_pagina(4));funcoes.verificar_riscos()
ui.btn_configs.clicked.connect(lambda: Functions.mudar_pagina(5))
ui.btn_ocultar.clicked.connect(lambda: Functions.ocultar_menu())



ui.btn_save_new_score.clicked.connect(Functions.salvar_score)
ui.btn_update_supplier.clicked.connect(funcoes.atualizar_dados_supplier)
ui.btn_info.clicked.connect(funcoes.mostrar_info)
ui.btn_register_new_supplier.clicked.connect(lambda: Functions.registrar_novo_usuario())
ui.btn_update_criteria.clicked.connect(lambda: funcoes.atualizar_criterios_no_banco())
ui.btn_vendor_score.clicked.connect(lambda: funcoes.abrir_janela_select_supplier("score"))
ui.btn_vendor_timeline.clicked.connect(lambda: funcoes.abrir_janela_select_supplier("timeline"))
ui.btn_vendor_register.clicked.connect(lambda: funcoes.abrir_janela_select_supplier("register"))


ui.btn_clear_register.clicked.connect(funcoes.apagar_registro_selecionado)
ui.btn_add_continuity.clicked.connect(funcoes.adicionar_continuity)
ui.btn_add_sourcing.clicked.connect(funcoes.adicionar_sourcing)
ui.btn_add_sqie.clicked.connect(funcoes.adicionar_sqie)
ui.btn_clear_new_register.clicked.connect(funcoes.apagar_todos_campos_register)
ui.btn_clear_score.clicked.connect(funcoes.apagar_todos_campos_query)
ui_register.btn_save_new_supplier.clicked.connect(funcoes.salvar_novo_supplier)
ui.btn_add_category.clicked.connect(funcoes.adicionar_category)
ui.btn_add_bu.clicked.connect(funcoes.adicionar_bu)
ui.btn_unlock_criteria_edit.clicked.connect(funcoes.comparar_senha_edicao_criteria)



# Alteração nos campos
ui.quality_package_input.textChanged.connect(lambda: Functions.total_score_calculate())
ui.quality_pickup_input.textChanged.connect(lambda: Functions.total_score_calculate())
ui.nil_input.textChanged.connect(lambda: Functions.total_score_calculate())
ui.otif_input.textChanged.connect(lambda: Functions.total_score_calculate())
#ui.vendor_register.currentTextChanged.connect(lambda: Functions.atualizar_campos_vendor_register())
ui.tabWidget.currentChanged.connect(lambda index: funcoes.carregar_graficos() if index == 1 else None)
ui_select.btn_select_vendor.clicked.connect(lambda:funcoes.selecionar_vendor_pelo_botao())
ui_select.table_select_supplier.cellDoubleClicked.connect(lambda:funcoes.selecionar_vendor_pelo_botao())



ui.tableDetails.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

funcoes.iniciar_splash()

#janela_principal.setFixedSize(janela_principal.size())
#janela_login.setFixedSize(janela_login.size())
janela_principal.setWindowFlags(
    QtCore.Qt.Window |
    QtCore.Qt.WindowMinimizeButtonHint |
    QtCore.Qt.WindowMaximizeButtonHint |
    QtCore.Qt.WindowCloseButtonHint
)


janela_login.show()

sys.exit(app.exec_())