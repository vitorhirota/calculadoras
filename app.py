import altair as alt
import numpy as np
import numpy_financial as npf
import pandas as pd
import streamlit as st
# import sympy as sp

from scipy.optimize import minimize_scalar

def find_n(n, nper, i, nper_adj, balance, interest, prev_installment):
    amortization = round(balance / (nper - i - nper_adj - n + 1), 2)
    return abs((amortization+interest)/prev_installment - 1)


def intro():
    st.write("# Bem vindo à Calculadora! 👋")
    st.sidebar.success("Selecione uma calculadora acima.")

    st.markdown(
        """
        Então vc quer calcular algumas coisas?"""
    )


def aposentadoria():
    st.write(
        f"""
        # {list(options.keys())[1]}

        Quanto poupar? Por quanto tempo? Essa calculadora é para você."""
    )
    st.sidebar.write("## Sobre você")
    age = st.sidebar.number_input("Sua idade", value=30)
    retirement_age = st.sidebar.number_input(
        "Sua expectativa de se aposentar",
        value=60,
        help="O momento em que você para de aportar ao seu fundo de aposentadoria.",
    )
    life_expectancy = st.sidebar.number_input(
        "Sua expectativa de vida",
        value=77,
        help="77 é a expectativa de vida média brasileira.",
    )
    revenue = st.sidebar.number_input(
        "Sua renda",
        value=5000,
        step=100,
        help="A primeira premissa, é a de que você manterá sua renda depois da aposentadoria.",
    )
    principal = st.sidebar.number_input(
        "Seu patrimônio atual",
        value=0,
        step=1000,
        help="Se você já tiver algo guardado para a aposentadoria.",
    )

    st.sidebar.write("## Sobre a economia")
    rate_interest = st.sidebar.number_input(
        "Estimativa % juros ao ano?", value=10.0, step=0.1, format="%.1f"
    )
    rate_inflation = st.sidebar.number_input(
        "Estimativa % inflação ao ano?", value=3.5, step=0.1, format="%.1f"
    )

    # params
    r = (1 + ((1 + rate_interest / 100) / (1 + rate_inflation / 100) - 1)) ** (
        1 / 12
    ) - 1
    nper1 = (retirement_age - age) * 12
    nper2 = (life_expectancy - retirement_age) * 12
    fv = npf.pv(r, nper2, -revenue)
    pmt = -npf.pmt(r, nper1, -principal, fv=fv)

    st.info(f"R$ **{fv:,.2f}**")
    st.write(
        f"É o valor necessário para viver por mais **{nper2/12:.0f}** anos (após os {retirement_age}), mantendo sua renda mensal de R\$ {revenue:,.2f}."
    )

    st.info(f"R$ **{pmt:,.2f}**")
    st.write(
        f"É o valor a ser investido por mês para construir seu fundo de aposentadoria."
    )

    st.subheader("Evolução")
    df = (
        pd.DataFrame(
            np.arange(start=1, stop=nper1 + nper2 + 1),
            columns=[
                "nper",
            ],
        )
        .assign(
            total=lambda x: np.where(
                x.nper <= nper1,
                npf.fv(r, x.nper, -pmt, -principal),
                npf.fv(r, x.nper - nper1, revenue, -fv),
            ),
        )
        .melt("nper")
    )
    # df

    ch = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("nper", title="Período"),
            y=alt.Y("value", title="Valor"),
            color="variable",
            # tooltip=['nper', 'number', 'Período'), 'principal']
        )
    )
    # st.altair_chart(c, use_container_width=True)

    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection_point(
        nearest=True, on="mouseover", fields=["nper"], empty=False
    )

    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = (
        alt.Chart(df)
        .mark_point()
        .encode(
            x=alt.X("nper", title="Período"),
            opacity=alt.value(0),
        )
        .add_params(nearest)
    )

    # Draw points on the line, and highlight based on selection
    points = ch.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = ch.mark_text(align="right", dx=-10, dy=-10).encode(
        text=alt.condition(nearest, "value:Q", alt.value(" "), format=",.2f")
    )

    # Draw a rule at retirement
    xrule = (
        alt.Chart(df)
        .mark_rule(color="white", strokeDash=[3, 3])
        .encode(
            x=alt.datum(nper1),
        )
    )

    # Draw a rule at the location of the selection
    rules = (
        alt.Chart(df)
        .mark_rule(color="gray")
        .encode(
            x="nper",
        )
        .transform_filter(nearest)
    )

    # Put the five layers into a chart and bind the data
    st.altair_chart(
        alt.layer(ch, selectors, points, xrule, rules, text).properties(height=400),
        use_container_width=True,
    )


def financiamento():
    st.write(
        f"""
        # {list(options.keys())[2]}

        Quer comprar uma casa financiada? Qual o valor total? Vale a pena alugar?

        A simulação abaixo considera um financiamento SAC, e desconsidera a taxa de seguro e de administração.
        """
    )

    # params
    price = st.sidebar.number_input("Valor da casa", value=500000, step=50000)
    down_paym = st.sidebar.slider("Valor entrada (%)", 20, 80, 20) / 100
    nper = st.sidebar.slider("Prazo (meses)", 0, 420, 420)
    rate_mortgage = (
        st.sidebar.number_input("Taxa de juros (%)", value=9.0, step=0.1) / 100
    )
    rate_tr = st.sidebar.number_input("Estimativa TR (%)", value=2.0, step=0.1) / 100
    rate_interest = (
        st.sidebar.number_input("Estimativa SELIC (%)", value=10.0, step=0.1) / 100
    )
    rate_inflation = (
        st.sidebar.number_input("Estimativa IPCA (%)", value=3.5, step=0.1) / 100
    )
    income = st.sidebar.number_input('Renda familiar bruta (R$)', value=15000, step=1000, help='Para cálculo de FGTS')

    # calculations
    rate_interest_m = (1 + rate_interest) ** (1 / 12) - 1
    rate_inflation_m = (1 + rate_inflation) ** (1 / 12) - 1
    r2 = (1 + rate_interest_m) / (1 + rate_inflation_m) - 1

    rate_tr_m = (1 + rate_tr) ** (1 / 12) - 1
    rate_mortgage_m = (1 + rate_mortgage) ** (1 / 12) - 1
    r = rate_mortgage_m * (1 + rate_tr_m)

    st.subheader("Evolução")
    st.write("Considerando o cenário base:")

    per = np.arange(start=1, stop=nper + 1)
    balance = price * (1 - down_paym)
    amortization = 0
    interest = 0
    principal1 = price * down_paym
    principal2 = price * down_paym
    balance1 = balance
    balance2 = balance
    nper_adj1 = 0
    nper_adj2 = 0
    amortization2 = 0
    max_amortization = 0
    xx = [(balance, amortization, interest, price, principal1, principal2)]
    for i in per:
        balance_adj = round(balance * (1 + rate_tr_m), 2)
        amortization = round(balance_adj / (nper - i + 1), 2)
        interest = round(balance * r, 2)
        balance = balance_adj - amortization

        years=int(i/12)
        price_adj = round(price * (1+rate_inflation)**years, 2)
        rent_adj = round(price_adj * 0.0035, 2)

        principal1 = round(principal1 * (1 + rate_interest_m) + (amortization + interest), 2)
        principal2 = round(principal2 * (1 + rate_interest_m) + max(amortization + interest - rent_adj, 0), 2)

        if balance1 >= 0:
            fgts = (income*0.08*24) * ((i % 24) == 1) * (i > 1)
            pre_balance1 = max(round(balance1 * (1 + rate_tr_m) - fgts, 2), 0)
            interest1 = max(round((balance1 - fgts) * r, 2), 0)
            if fgts:
                nper1 = minimize_scalar(find_n, args=(nper, i, nper_adj1, pre_balance1, interest1, installment1_prev))
                nper_adj1 += round(nper1.x, 0)
            amortization1 = round(pre_balance1 / (nper - i - nper_adj1 + 1), 2)
            balance1 = round(pre_balance1 - amortization1, 2)
            installment1_prev = (amortization1 + interest1)
        else:
            fgts, amortization1, interest1 = [None, ]*3

        max_amortization = max(max_amortization, (amortization+interest))
        if round(balance2, 0) >= 0:
            extra = max(max_amortization - installment2_prev, 0) if amortization2 else 0
            pre_balance2 = max(round(balance2 * (1 + rate_tr_m) - extra, 2), 0)
            interest2 = max(round((balance2 - extra) * r, 2), 0)
            if extra:
                nper2 = minimize_scalar(find_n, args=(nper, i, nper_adj2, pre_balance2, interest2, installment2_prev))
                nper_adj2 += round(nper2.x, 0)
            amortization2 = round(pre_balance2 / (nper - i - nper_adj2 + 1), 2)
            balance2 = round(pre_balance2 - amortization2, 2)
            installment2_prev = (amortization2 + interest2)
        else:
            extra, amortization1, interest2 = [None, ]*3

        xx.append((balance, amortization, interest,
                   price_adj, principal1, principal2, rent_adj,
                   balance1, fgts, nper_adj1, amortization1, interest1,
                   balance2, extra, nper_adj2, amortization2, interest2,
                   max_amortization
                   ))

    df = (
        pd.DataFrame(
            xx,
            columns=["balance", "amortization", "interest",
                     'price_adj', "principal1", "principal2", 'rent_adj',
                     'balance1', 'fgts', 'nper_adj1', 'amortization1', 'interest1',
                     'balance2', 'extra', 'nper_adj2', 'amortization2', 'interest2',
                    'max_amortization'
                     ],
        )
        .reset_index(names=["nper"])
        .assign(
            total2=lambda x: x.amortization2 + x.interest2,
            ttotal2=lambda x: x.amortization2 + x.interest2 + x.extra,
            total1=lambda x: x.amortization1 + x.interest1,
            anos=lambda x: x.nper / 12,
            total=lambda x: x.amortization + x.interest,
        )
        # .melt("nper")
    )
    st.write(df.set_index('nper'))

    base = alt.Chart(df.query("nper > 0").melt("anos")).encode(
        x=alt.X("anos").axis(title="Anos")
    )

    installments = (
        base.mark_line()
        .encode(y=alt.Y("value", title="Valor"), color="variable")
        .transform_filter(
            alt.FieldOneOfPredicate(
                field="variable", oneOf=["amortization", "interest", "total",
                                         "amortization1", 'interest1', 'total1',
                                         "amortization2", 'interest2', 'total2',
                                         ]
            )
        )
    )

    balance = (
        base.mark_line()
        .encode(y=alt.Y("value", title="Saldo Devedor"), color="variable")
        .transform_filter(
            alt.FieldOneOfPredicate(
                field="variable", oneOf=["balance", "balance1", "balance2", ]
            )
        )
    )

    # balance = alt.Chart(df).mark_line().encode(x="anos", y="balance")

    st.altair_chart(
        # (installments+balance),
        alt.layer(installments, balance).resolve_scale(y="independent"),
        use_container_width=True,
    )

    st.header("Financiamento vs Aluguel")

    st.write(
        f"""
        O valor total pago no cenário base é de R$ {df.total.sum():,.2f}. **{df.total.sum()/price:,.1f}x** mais que o valor da casa (considerando seu valor hoje).

        Podemos avaliar por duas perspectivas: prazo, e patrimonio final.

        Vamos avaliar alguns cenários.
        """
    )

    pmt = st.number_input('Aplicação mensal', 2000, step=100)
    n1 = df.query("principal1 > price_adj").head(1).nper.values[0]
    n2 = df.query("principal2 > price_adj").head(1).nper.values[0]
    n3 = npf.nper(r2, pmt, price*0.2, -price)
    st.markdown(f"""
        ### Investir enquanto paga aluguel

        Cenários em que investimos o valor até alcançar o valor da casa.

        | Cenário | Descrição | Prazo |
        | ------- | ----- | ----- |
        | 1 | Investir o mesmo valor da parcela de financiamento | {n1} meses ({n1/12:.1f} anos) |
        | 2 | Investir a diferença da parcela e o aluguel | {n2} meses ({n2/12:.1f} anos) |
        | 3 | Investir um valor fixo de R$ {pmt:,.2f} | {n3:.0f} meses ({n3/12:.1f} anos) |

        Todos os cenários usam taxas nominais, e correção anual do imóvel à inflação estimada (e por conseguinte o valor do aluguel também).
    """)

    tt = df.total.sum()
    n1 = df.query("balance1 == 0").head(1).nper.values[0]
    j1 = df.query("balance1 > 0").total1.sum()
    n2 = df.query("balance2 == 0").head(1).nper.values[0]
    j2 = df.query("balance2 > 0").total2.sum()
    st.markdown(f"""
        ### Amortizações

        Amortizações de prazo diminuem a carga de juros, pois, como as prestações devem ficar constantes, o valor amortizado deve subir.

        | Cenário | Descrição | Prazo quitação | Amortização (R\$) | Prestação (% / cenário base) |
        | ------- | ----- | ----- | ----- | ----- |
        | 1 | Amortização de FGTS a cada dois anos | {n1} meses ({n1/12:.1f} anos) | R\$ {df.fgts.sum():,.2f} | R$ {j1:,.2f} ({j1/tt - 1:.1%}) |
        | 2 | Se o valor da parcela fosse constante | {n2} meses ({n2/12:.1f} anos) | R\$ {df.extra.sum():,.2f} | R$ {j2:,.2f} ({j2/tt - 1:.1%}) |
    """)
        # | 3 | Amortização de 2 parcela a cada 12 meses | {n3:.0f} meses ({n3/12:.1f} anos) | - | - |

    #
    # st.subheader("4. Amortizações extras")
    # edited_df = st.experimental_data_editor(df)
    # favorite_command = edited_df.loc[edited_df["rating"].idxmax()]["command"]
    # st.markdown(f"Your favorite command is **{favorite_command}** 🎈")



options = {
    "—": intro,
    "Aposentadoria": aposentadoria,
    "Financiamento": financiamento,
}

st.sidebar.title("Caculadoras")
fn = st.sidebar.selectbox("Selecione uma opção", options.keys())
options[fn]()
