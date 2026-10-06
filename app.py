import streamlit as st
import pandas as pd
import cv2
import numpy as np
import requests
import zxingcpp
import os
from datetime import date

from database import (
    verify_user,
    create_user,
    get_product_by_barcode,
    save_barcode_product,
    add_product,
    get_all_products,
    get_status_counts,
    search_products,
    get_products_by_status,
    delete_product,
    delete_all_products
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Smart Expiry Scanner",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"

if "barcode" not in st.session_state:
    st.session_state.barcode = ""

if "scanned_product" not in st.session_state:
    st.session_state.scanned_product = None

if "manual_mode" not in st.session_state:
    st.session_state.manual_mode = False

if "current_image_path" not in st.session_state:
    st.session_state.current_image_path = ""


# =========================================================
# THEME / CSS
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       GENERAL APP
       ===================================================== */

    .stApp {
        background:
            radial-gradient(
                circle at 0% 0%,
                rgba(91, 95, 239, 0.12),
                transparent 25%
            ),
            radial-gradient(
                circle at 100% 0%,
                rgba(139, 92, 246, 0.10),
                transparent 25%
            ),
            var(--background-color);
    }

    .main .block-container {
        max-width: 1200px;
        padding-top: 35px;
        padding-bottom: 50px;
    }


    /* =====================================================
       SIDEBAR
       ===================================================== */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                rgba(91, 95, 239, 0.08),
                rgba(139, 92, 246, 0.04)
            ),
            var(--secondary-background-color);

        border-right: 1px solid var(--border-color);
    }

    section[data-testid="stSidebar"] > div {
        padding: 24px 18px;
    }

    section[data-testid="stSidebar"] h1 {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    section[data-testid="stSidebar"] .stCaption {
        opacity: 0.75;
    }


    /* Sidebar navigation */

    section[data-testid="stSidebar"]
    div[role="radiogroup"] {
        gap: 7px;
    }

    section[data-testid="stSidebar"]
    div[role="radiogroup"] label {
        border-radius: 12px;
        padding: 9px 12px;
        border: 1px solid transparent;
        transition: 0.2s ease;
    }

    section[data-testid="stSidebar"]
    div[role="radiogroup"] label:hover {
        background: rgba(91, 95, 239, 0.10);
        border-color: rgba(91, 95, 239, 0.18);
    }

    section[data-testid="stSidebar"]
    div[role="radiogroup"] label p {
        font-weight: 600;
    }


    /* =====================================================
       CONTAINERS / CARDS
       ===================================================== */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--secondary-background-color);
        border: 1px solid var(--border-color);
        border-radius: 18px;
        box-shadow:
            0 8px 25px rgba(30, 41, 80, 0.08);
    }


    /* =====================================================
       BUTTONS
       ===================================================== */

    .stButton > button {
        min-height: 43px;
        border-radius: 11px;

        background: #5b5fef;
        color: #ffffff;

        border: 1px solid #5b5fef;

        font-weight: 700;

        transition:
            transform 0.15s ease,
            box-shadow 0.15s ease,
            background 0.15s ease;
    }

    .stButton > button:hover {
        background: #4f54d9;
        border-color: #4f54d9;
        color: #ffffff;

        transform: translateY(-1px);

        box-shadow:
            0 7px 18px rgba(91, 95, 239, 0.25);
    }


    /* =====================================================
       INPUTS
       ===================================================== */

    .stTextInput input,
    .stNumberInput input,
    .stDateInput input {
        border-radius: 10px;
        border: 1px solid var(--border-color);
        background: var(--secondary-background-color);
        color: var(--text-color);
    }

    .stTextInput input:focus,
    .stNumberInput input:focus,
    .stDateInput input:focus {
        border-color: #5b5fef;
        box-shadow:
            0 0 0 2px rgba(91, 95, 239, 0.15);
    }


    /* =====================================================
       SELECTBOX
       ===================================================== */

    div[data-baseweb="select"] > div {
        border-radius: 10px;
        border-color: var(--border-color);
        background: var(--secondary-background-color);
    }


    /* =====================================================
       FILE UPLOADER
       ===================================================== */

    section[data-testid="stFileUploaderDropzone"] {
        border-radius: 15px;
        border: 1.5px dashed #7b7ff0;
        background: rgba(91, 95, 239, 0.04);
    }


    /* =====================================================
       METRICS
       ===================================================== */

    div[data-testid="stMetric"] {
        background: var(--secondary-background-color);

        border: 1px solid var(--border-color);

        border-radius: 16px;

        padding: 16px;

        box-shadow:
            0 6px 18px rgba(30, 41, 80, 0.07);
    }


    /* =====================================================
       DATAFRAME
       ===================================================== */

    div[data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid var(--border-color);
    }


    /* =====================================================
       ALERTS
       ===================================================== */

    div[data-testid="stAlert"] {
        border-radius: 12px;
    }


    /* =====================================================
       DIVIDERS
       ===================================================== */

    hr {
        border-color: var(--border-color);
    }


    /* =====================================================
       HEADINGS
       ===================================================== */

    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.8px;
    }

    h2 {
        font-weight: 750 !important;
    }

    h3 {
        font-weight: 700 !important;
    }


    /* =====================================================
       LOGIN / SIGNUP SPACING
       ===================================================== */

    .auth-space {
        margin-top: 70px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# LOGIN PAGE
# =========================================================

def login_page():

    st.write("")

    left, center, right = st.columns(
        [1, 1.4, 1]
    )

    with center:

        st.title("Smart Expiry Scanner")

        st.caption(
            "Smart inventory and expiry management"
        )

        st.write("")

        with st.container(border=True):

            st.subheader("Welcome Back")

            st.write(
                "Login to access your inventory dashboard."
            )

            st.write("")

            username = st.text_input(
                "Username",
                key="login_username",
                placeholder="Enter your username"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
                placeholder="Enter your password"
            )

            st.write("")

            login_col, signup_col = st.columns(2)

            with login_col:

                if st.button(
                    "Login",
                    use_container_width=True,
                    key="login_button"
                ):

                    if not username.strip():

                        st.error(
                            "Please enter your username."
                        )

                    elif not password:

                        st.error(
                            "Please enter your password."
                        )

                    elif verify_user(
                        username,
                        password
                    ):

                        st.session_state.logged_in = True
                        st.session_state.username = username.strip()
                        st.session_state.current_page = "Home"

                        st.rerun()

                    else:

                        st.error(
                            "Invalid username or password."
                        )

            with signup_col:

                if st.button(
                    "Sign Up",
                    use_container_width=True,
                    key="signup_button"
                ):

                    st.session_state.auth_page = "signup"

                    st.rerun()


# =========================================================
# SIGNUP PAGE
# =========================================================

def signup_page():

    st.write("")

    left, center, right = st.columns(
        [1, 1.4, 1]
    )

    with center:

        st.title("Create Account")

        st.caption(
            "Create an account to manage your inventory."
        )

        st.write("")

        with st.container(border=True):

            st.subheader("Sign Up")

            username = st.text_input(
                "Username",
                key="signup_username",
                placeholder="Choose a username"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="signup_password",
                placeholder="Create a password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                key="signup_confirm_password",
                placeholder="Enter your password again"
            )

            st.write("")

            create_col, back_col = st.columns(2)

            with create_col:

                if st.button(
                    "Create Account",
                    use_container_width=True,
                    key="create_account"
                ):

                    if not username.strip():

                        st.error(
                            "Username is required."
                        )

                    elif len(username.strip()) < 3:

                        st.error(
                            "Username must contain at least 3 characters."
                        )

                    elif not password:

                        st.error(
                            "Password is required."
                        )

                    elif len(password) < 6:

                        st.error(
                            "Password must contain at least 6 characters."
                        )

                    elif password != confirm_password:

                        st.error(
                            "Passwords do not match."
                        )

                    else:

                        success, message = create_user(
                            username.strip(),
                            password
                        )

                        if success:

                            st.success(
                                "Account created successfully."
                            )

                            st.session_state.auth_page = "login"

                            st.info(
                                "Please login with your new account."
                            )

                        else:

                            st.error(
                                message
                            )

            with back_col:

                if st.button(
                    "Back to Login",
                    use_container_width=True,
                    key="back_login"
                ):

                    st.session_state.auth_page = "login"

                    st.rerun()


# =========================================================
# SIDEBAR
# =========================================================

def show_sidebar():

    with st.sidebar:

        st.title("📦 Smart Expiry")

        st.caption(
            "INVENTORY MANAGEMENT"
        )

        st.divider()

        st.caption(
            "SIGNED IN AS"
        )

        st.write(
            f"**{st.session_state.username}**"
        )

        st.divider()

        st.caption(
            "MENU"
        )

        pages = [
            "🏠 Home",
            "📷 Scanner",
            "📊 Dashboard",
            "📁 Excel Import"
        ]

        page_mapping = {
            "🏠 Home": "Home",
            "📷 Scanner": "Scanner",
            "📊 Dashboard": "Dashboard",
            "📁 Excel Import": "Excel Import"
        }

        current_display = None

        for display_name, page_name in page_mapping.items():

            if page_name == st.session_state.current_page:

                current_display = display_name

        selected_display = st.radio(
            "Navigation",
            pages,
            index=pages.index(
                current_display
            ),
            label_visibility="collapsed"
        )

        selected_page = page_mapping[
            selected_display
        ]

        if selected_page != st.session_state.current_page:

            st.session_state.current_page = selected_page

            st.rerun()

        st.divider()

        st.caption(
            "ACCOUNT"
        )

        if st.button(
            "Logout",
            use_container_width=True,
            key="logout_button"
        ):

            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.current_page = "Home"
            st.session_state.barcode = ""
            st.session_state.scanned_product = None
            st.session_state.manual_mode = False
            st.session_state.current_image_path = ""

            st.rerun()


# =========================================================
# HOME PAGE
# =========================================================

def home_page():

    st.title("Smart Expiry Scanner")

    st.caption(
        "Scan products, manage your inventory and stay ahead of expiry dates."
    )

    st.write("")

    col1, col2, col3 = st.columns(
        3,
        gap="large"
    )

    # -----------------------------------------------------
    # SCANNER
    # -----------------------------------------------------

    with col1:

        with st.container(border=True):

            st.subheader("📷 Scanner")

            st.write(
                "Scan product barcodes and quickly add "
                "package details to your inventory."
            )

            st.write("")

            if st.button(
                "Open Scanner",
                use_container_width=True,
                key="home_scanner"
            ):

                st.session_state.current_page = "Scanner"

                st.rerun()

    # -----------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------

    with col2:

        with st.container(border=True):

            st.subheader("📊 Dashboard")

            st.write(
                "Monitor inventory, expiry dates and "
                "product status from one place."
            )

            st.write("")

            if st.button(
                "Open Dashboard",
                use_container_width=True,
                key="home_dashboard"
            ):

                st.session_state.current_page = "Dashboard"

                st.rerun()

    # -----------------------------------------------------
    # EXCEL
    # -----------------------------------------------------

    with col3:

        with st.container(border=True):

            st.subheader("📁 Excel Import")

            st.write(
                "Import multiple products quickly using "
                "CSV or Excel files."
            )

            st.write("")

            if st.button(
                "Open Excel Import",
                use_container_width=True,
                key="home_excel"
            ):

                st.session_state.current_page = "Excel Import"

                st.rerun()

    st.write("")

    st.divider()

    st.caption(
        "Smart Expiry Scanner • Inventory made simple"
    )


# =========================================================
# BARCODE DETECTION
# =========================================================

def detect_barcode(image):

    try:

        image_array = np.asarray(
            bytearray(
                image.getvalue()
            ),
            dtype=np.uint8
        )

        frame = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if frame is None:
            return None

        results = zxingcpp.read_barcodes(
            frame
        )

        for result in results:

            if result.text:

                return result.text

    except Exception as error:

        st.error(
            f"Barcode detection error: {error}"
        )

    return None


# =========================================================
# OPEN FOOD FACTS SEARCH
# =========================================================

def search_open_food_facts(barcode):

    try:

        url = (
            "https://world.openfoodfacts.org/api/v2/product/"
            + str(barcode)
        )

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:

            return None

        data = response.json()

        if data.get("status") != 1:

            return None

        product = data.get(
            "product",
            {}
        )

        return {
            "product_name": product.get(
                "product_name",
                ""
            ),
            "brand": product.get(
                "brands",
                ""
            ),
            "category": product.get(
                "categories",
                ""
            ),
            "image_url": product.get(
                "image_front_url",
                ""
            )
        }

    except Exception as error:

        st.error(
            f"Online search failed: {error}"
        )

        return None


# =========================================================
# SAVE UPLOADED IMAGE
# =========================================================

def save_uploaded_image(
    uploaded_file,
    barcode
):

    if uploaded_file is None:

        return ""

    try:

        os.makedirs(
            "product_images",
            exist_ok=True
        )

        extension = os.path.splitext(
            uploaded_file.name
        )[1]

        if not extension:

            extension = ".jpg"

        safe_name = uploaded_file.name.replace(
            " ",
            "_"
        )

        file_path = os.path.join(
            "product_images",
            f"{barcode}_{safe_name}"
        )

        with open(
            file_path,
            "wb"
        ) as file:

            file.write(
                uploaded_file.getbuffer()
            )

        return file_path

    except Exception:

        return ""


# =========================================================
# SAVE ONLINE IMAGE
# =========================================================

def save_online_image(
    image_url,
    barcode
):

    if not image_url:

        return ""

    try:

        os.makedirs(
            "product_images",
            exist_ok=True
        )

        response = requests.get(
            image_url,
            timeout=10
        )

        if response.status_code == 200:

            file_path = os.path.join(
                "product_images",
                f"{barcode}.jpg"
            )

            with open(
                file_path,
                "wb"
            ) as file:

                file.write(
                    response.content
                )

            return file_path

    except Exception:

        pass

    return ""


# =========================================================
# SCANNER PAGE
# =========================================================

def scanner_page():

    st.title("Product Scanner")

    st.caption(
        "Scan a barcode or register a product manually."
    )

    st.divider()

    st.subheader("Upload Product Image")

    uploaded_file = st.file_uploader(
        "Choose an image containing the barcode",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]
    )

    if uploaded_file:

        st.image(
            uploaded_file,
            caption="Product Image",
            width=350
        )

        if st.button(
            "Scan Barcode",
            use_container_width=True,
            key="scan_barcode"
        ):

            barcode = detect_barcode(
                uploaded_file
            )

            if barcode:

                st.session_state.barcode = barcode

                st.success(
                    f"Barcode detected: {barcode}"
                )

                local_product = get_product_by_barcode(
                    barcode
                )

                if local_product:

                    st.session_state.scanned_product = {
                        "product_name": local_product[
                            "product_name"
                        ],
                        "brand": local_product[
                            "brand"
                        ],
                        "category": local_product[
                            "category"
                        ]
                    }

                    st.session_state.manual_mode = False

                    st.session_state.current_image_path = (
                        save_uploaded_image(
                            uploaded_file,
                            barcode
                        )
                    )

                    st.rerun()

                else:

                    st.session_state.scanned_product = None
                    st.session_state.manual_mode = False

            else:

                st.warning(
                    "No barcode detected. You can register the product manually."
                )

                st.session_state.manual_mode = True

    # =====================================================
    # LOCAL PRODUCT FOUND
    # =====================================================

    if (
        st.session_state.barcode
        and st.session_state.scanned_product
    ):

        product = st.session_state.scanned_product

        st.divider()

        st.subheader("Product Found")

        with st.container(border=True):

            st.write(
                f"**Product:** {product['product_name']}"
            )

            st.write(
                f"**Brand:** {product['brand'] or 'N/A'}"
            )

            st.write(
                f"**Category:** {product['category'] or 'N/A'}"
            )

        st.divider()

        st.subheader("Package Details")

        with st.form(
            "known_product_form"
        ):

            col1, col2 = st.columns(2)

            with col1:

                name = st.text_input(
                    "Product Name",
                    value=product["product_name"]
                )

                brand = st.text_input(
                    "Brand",
                    value=product["brand"]
                )

                category = st.text_input(
                    "Category",
                    value=product["category"]
                )

                quantity = st.number_input(
                    "Quantity",
                    min_value=1,
                    value=1
                )

            with col2:

                batch_number = st.text_input(
                    "Batch Number"
                )

                expiry_date = st.date_input(
                    "Expiry Date",
                    value=date.today()
                )

                storage_location = st.text_input(
                    "Storage Location"
                )

                barcode = st.text_input(
                    "Barcode",
                    value=st.session_state.barcode
                )

            save_button = st.form_submit_button(
                "Save Product",
                use_container_width=True
            )

        if save_button:

            if not name.strip():

                st.error(
                    "Product name is required."
                )

            else:

                add_product(
                    product_name=name,
                    brand=brand,
                    category=category,
                    quantity=quantity,
                    batch_number=batch_number,
                    barcode=barcode,
                    expiry_date=expiry_date.isoformat(),
                    storage_location=storage_location,
                    image_path=st.session_state.current_image_path
                )

                st.success(
                    f"{name} added to inventory successfully."
                )

                st.session_state.barcode = ""
                st.session_state.scanned_product = None
                st.session_state.current_image_path = ""

                st.rerun()

    # =====================================================
    # UNKNOWN BARCODE
    # =====================================================

    elif (
        st.session_state.barcode
        and not st.session_state.scanned_product
    ):

        st.divider()

        st.subheader("Barcode Not Found")

        st.write(
            f"Detected barcode: **{st.session_state.barcode}**"
        )

        st.info(
            "This barcode is not stored in your local database yet."
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "Search Online",
                use_container_width=True,
                key="online_search"
            ):

                with st.spinner(
                    "Searching Open Food Facts..."
                ):

                    online_product = search_open_food_facts(
                        st.session_state.barcode
                    )

                if online_product:

                    save_barcode_product(
                        barcode=st.session_state.barcode,
                        product_name=online_product[
                            "product_name"
                        ],
                        brand=online_product[
                            "brand"
                        ],
                        category=online_product[
                            "category"
                        ]
                    )

                    st.session_state.scanned_product = (
                        online_product
                    )

                    st.session_state.current_image_path = (
                        save_online_image(
                            online_product["image_url"],
                            st.session_state.barcode
                        )
                    )

                    st.success(
                        "Product found and saved locally."
                    )

                    st.rerun()

                else:

                    st.warning(
                        "Product was not found online. Please register it manually."
                    )

                    st.session_state.manual_mode = True

        with col2:

            if st.button(
                "Register Manually",
                use_container_width=True,
                key="manual_unknown"
            ):

                st.session_state.manual_mode = True

                st.rerun()

    # =====================================================
    # MANUAL REGISTRATION
    # =====================================================

    if st.session_state.manual_mode:

        st.divider()

        st.subheader(
            "Manual Product Registration"
        )

        manual_image = st.file_uploader(
            "Upload Product Picture",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ],
            key="manual_product_image"
        )

        manual_barcode = st.text_input(
            "Barcode (optional)",
            value=st.session_state.barcode
        )

        with st.form(
            "manual_product_form"
        ):

            col1, col2 = st.columns(2)

            with col1:

                name = st.text_input(
                    "Product Name"
                )

                brand = st.text_input(
                    "Brand"
                )

                category = st.text_input(
                    "Category"
                )

                quantity = st.number_input(
                    "Quantity",
                    min_value=1,
                    value=1
                )

            with col2:

                batch_number = st.text_input(
                    "Batch Number"
                )

                expiry_date = st.date_input(
                    "Expiry Date",
                    value=date.today()
                )

                storage_location = st.text_input(
                    "Storage Location"
                )

            save_button = st.form_submit_button(
                "Save Product",
                use_container_width=True
            )

        if save_button:

            if not name.strip():

                st.error(
                    "Product name is required."
                )

            else:

                image_path = ""

                if manual_image:

                    image_path = save_uploaded_image(
                        manual_image,
                        manual_barcode or "manual"
                    )

                add_product(
                    product_name=name,
                    brand=brand,
                    category=category,
                    quantity=quantity,
                    batch_number=batch_number,
                    barcode=manual_barcode,
                    expiry_date=expiry_date.isoformat(),
                    storage_location=storage_location,
                    image_path=image_path
                )

                if manual_barcode.strip():

                    save_barcode_product(
                        barcode=manual_barcode,
                        product_name=name,
                        brand=brand,
                        category=category
                    )

                st.success(
                    f"{name} saved successfully."
                )

                st.session_state.manual_mode = False
                st.session_state.barcode = ""
                st.session_state.scanned_product = None
                st.session_state.current_image_path = ""

                st.rerun()

    # =====================================================
    # MANUAL WITHOUT BARCODE
    # =====================================================

    st.divider()

    if st.button(
        "Register Product Without Barcode",
        use_container_width=True,
        key="manual_no_barcode"
    ):

        st.session_state.manual_mode = True
        st.session_state.barcode = ""
        st.session_state.scanned_product = None

        st.rerun()


# =========================================================
# DASHBOARD
# =========================================================

def dashboard_page():

    st.title("Inventory Dashboard")

    st.caption(
        "Monitor products and their expiry status."
    )

    counts = get_status_counts()

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Safe",
            counts["Safe"]
        )

    with col2:

        st.metric(
            "Attention",
            counts["Attention"]
        )

    with col3:

        st.metric(
            "Urgent",
            counts["Urgent"]
        )

    with col4:

        st.metric(
            "Expired",
            counts["Expired"]
        )

    st.divider()

    search_text = st.text_input(
        "Search Inventory",
        placeholder="Search by name, brand, barcode or batch..."
    )

    status_filter = st.selectbox(
        "Filter by Status",
        [
            "All",
            "Safe",
            "Attention",
            "Urgent",
            "Expired",
            "Unknown"
        ]
    )

    if search_text.strip():

        products = search_products(
            search_text
        )

    elif status_filter != "All":

        products = get_products_by_status(
            status_filter
        )

    else:

        products = get_all_products()

    st.subheader(
        f"Inventory • {len(products)} product(s)"
    )

    if not products:

        st.info(
            "No products found."
        )

    for product in products:

        with st.container(border=True):

            col1, col2, col3 = st.columns(
                [1, 3, 1]
            )

            with col1:

                image_path = product["image_path"]

                if (
                    image_path
                    and os.path.exists(image_path)
                ):

                    st.image(
                        image_path,
                        width=130
                    )

                else:

                    st.caption(
                        "No image"
                    )

            with col2:

                st.subheader(
                    product["product_name"]
                )

                st.write(
                    f"**Brand:** {product['brand'] or 'N/A'}"
                )

                st.write(
                    f"**Category:** {product['category'] or 'N/A'}"
                )

                st.write(
                    f"**Quantity:** {product['quantity']}"
                )

                st.write(
                    f"**Batch:** {product['batch_number'] or 'N/A'}"
                )

                st.write(
                    f"**Barcode:** {product['barcode'] or 'N/A'}"
                )

                st.write(
                    f"**Expiry:** {product['expiry_date'] or 'N/A'}"
                )

                st.write(
                    f"**Storage:** {product['storage_location'] or 'N/A'}"
                )

                st.write(
                    f"**Status:** {product['status']}"
                )

            with col3:

                if st.button(
                    "Delete",
                    key=f"delete_{product['id']}"
                ):

                    delete_product(
                        product["id"]
                    )

                    st.rerun()

    if products:

        st.divider()

        if st.button(
            "Delete All Products",
            use_container_width=True,
            key="delete_all"
        ):

            delete_all_products()

            st.success(
                "All products deleted."
            )

            st.rerun()


# =========================================================
# EXCEL IMPORT
# =========================================================

def excel_import_page():

    st.title("Excel Import")

    st.caption(
        "Import multiple products into your inventory."
    )

    with st.container(border=True):

        st.subheader(
            "Required Columns"
        )

        st.write(
            "product_name, brand, category, quantity, "
            "batch_number, barcode, expiry_date, storage_location"
        )

    st.write("")

    template = pd.DataFrame(
        [
            {
                "product_name": "Milk",
                "brand": "Example Brand",
                "category": "Dairy",
                "quantity": 2,
                "batch_number": "B001",
                "barcode": "8901234567890",
                "expiry_date": "2026-10-20",
                "storage_location": "Refrigerator"
            }
        ]
    )

    st.download_button(
        "Download CSV Template",
        data=template.to_csv(index=False),
        file_name="expiry_scanner_template.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.divider()

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel File",
        type=[
            "csv",
            "xlsx",
            "xls"
        ]
    )

    if uploaded_file:

        try:

            if uploaded_file.name.lower().endswith(
                ".csv"
            ):

                df = pd.read_csv(
                    uploaded_file
                )

            else:

                df = pd.read_excel(
                    uploaded_file
                )

            st.subheader(
                "Preview"
            )

            st.dataframe(
                df,
                use_container_width=True
            )

            required_columns = [
                "product_name",
                "brand",
                "category",
                "quantity",
                "batch_number",
                "barcode",
                "expiry_date",
                "storage_location"
            ]

            missing_columns = [
                column
                for column in required_columns
                if column not in df.columns
            ]

            if missing_columns:

                st.error(
                    "Missing columns: "
                    + ", ".join(missing_columns)
                )

            else:

                if st.button(
                    "Import Products",
                    use_container_width=True,
                    key="import_products"
                ):

                    imported = 0

                    for _, row in df.iterrows():

                        try:

                            add_product(
                                product_name=str(
                                    row["product_name"]
                                ),
                                brand=str(
                                    row["brand"]
                                ),
                                category=str(
                                    row["category"]
                                ),
                                quantity=int(
                                    row["quantity"]
                                ),
                                batch_number=str(
                                    row["batch_number"]
                                ),
                                barcode=str(
                                    row["barcode"]
                                ),
                                expiry_date=str(
                                    row["expiry_date"]
                                ),
                                storage_location=str(
                                    row["storage_location"]
                                )
                            )

                            imported += 1

                        except Exception as error:

                            st.warning(
                                f"Could not import one row: {error}"
                            )

                    st.success(
                        f"{imported} product(s) imported successfully."
                    )

        except Exception as error:

            st.error(
                f"Could not read the file: {error}"
            )


# =========================================================
# START APPLICATION
# =========================================================

if not st.session_state.logged_in:

    if st.session_state.auth_page == "signup":

        signup_page()

    else:

        login_page()

else:

    show_sidebar()

    if st.session_state.current_page == "Home":

        home_page()

    elif st.session_state.current_page == "Scanner":

        scanner_page()

    elif st.session_state.current_page == "Dashboard":

        dashboard_page()

    elif st.session_state.current_page == "Excel Import":

        excel_import_page()