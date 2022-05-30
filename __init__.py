
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
import random
import calendar
from datetime import time, timedelta, datetime

from Forms import (
    RegistrationForm,
    LoginForm,
    UpdateProfileForm,
    SearchGymForm,
    MembershipCheckoutForm,
    MembershipUpdateForm,
    GymCheckoutForm
)
from GymLocation import GymLocation, Coordinates, CapacityLevel, generate_random_locations, CreateGymLocationForm
from User import User, generate_admin_user, admin_required
from FormsContact import CreateContactForm
from SubmittedContact import SubmittedContact
from SlotDetails import ClassSlotDetails, SlotDetails
from FormsReply import CreateReplyField
from Membership import Membership
from TimeSlot import TimeSlot, UpdateTimeSlotForm, CreateTimeSlotForm
from BookedGymSlot import BookedGymSlot
from util import get_nearest_date_from_day


current_user: User = current_user

app = Flask(__name__)
app.secret_key = b'*\x93\x00\xcb\x8f\xdb^+\xe8!H}x\x96\x85\xe71\x91s\x90\xae\xb3\t\xf5'

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "An account is required to access that page"
login_manager.login_message_category = "error"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.load_user(user_id)


@app.route("/")
def home():
    return render_template("public/home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm(request.form)
    if request.method == "POST" and login_form.validate():
        user = User.authenticate(login_form.username.data, login_form.password.data)
        if user is not None:
            login_user(user)
            next_view = request.args.get("next")
            if next_view is not None:
                return redirect(next_view)
            if user.is_admin:
                return redirect(url_for("admin_home"))
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password", "error")
    return render_template("public/login.html", form=login_form)


@app.route("/register", methods=["GET", "POST"])
def register():
    registration_form = RegistrationForm(request.form)
    if request.method == "POST" and registration_form.validate():
        user = User(
            registration_form.username.data,
            registration_form.email.data,
            registration_form.password.data,
            False
        )
        login_user(user)
        return redirect(url_for("home"))
    return render_template("public/register.html", form=registration_form)


@app.route("/logout")
@login_required  # to do: handle unauthorized access
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
    all_slots = list(SlotDetails.db.dict().values())
    class_slots = []
    for slot in all_slots:
        if slot.get_id() in current_user.slot_id_list:
            if slot.get_type() == "class":
                class_slots.append(slot)

    booked_gym_slots = BookedGymSlot.filter_by_user(current_user.user_id)

    membership_id = current_user.membership_id
    membership = Membership.db.get(membership_id)
    # to do: make slots user-specific
    return render_template(
        "public/profile.html",
        class_slots=class_slots,
        booked_gym_slots=booked_gym_slots,
        membership=membership
    )


@app.route("/profile/update", methods=["GET", "POST"])
@login_required
def update_profile():
    update_profile_form = UpdateProfileForm(request.form)
    if request.method == "POST" and update_profile_form.validate():
        updated = False

        user_id = current_user.get_id()
        user = User.load_user(user_id)

        # only update changed details
        if update_profile_form.username.data.lower() != user.username:
            user.username = update_profile_form.username.data
            updated = True

        if update_profile_form.email.data.lower() != user.email:
            user.email = update_profile_form.email.data
            updated = True

        if len(update_profile_form.new_password.data) > 0:
            user.password = update_profile_form.new_password.data
            updated = True

        if updated:
            User.update_user(user_id, user)
            return redirect(url_for("profile"))
        else:
            flash("Your details are still the same!", "error")
    elif request.method == "GET":
        update_profile_form.username.data = current_user.username
        update_profile_form.email.data = current_user.email
    return render_template("public/update_profile.html", form=update_profile_form)


@app.route("/profile/gym_slot/<booked_slot_id>", methods=["GET", "POST"])
@login_required
def profile_gym_slot(booked_slot_id):
    booked_slot = BookedGymSlot.db.get(booked_slot_id)
    if booked_slot is None:
        flash("Error: Unable to find slot details as it is not in database", "error")
        return redirect(url_for("profile"))

    gym_location = GymLocation.get(booked_slot.gym_id)
    if gym_location is None:
        flash("Error: Unable to find gym as it is not in the database", "error")
        return redirect(url_for("profile"))

    time_slot = TimeSlot.db.get(booked_slot.time_slot_id)
    if time_slot is None:
        flash("Could not find time slot in database", "error")
        return redirect(url_for("profile"))

    return render_template(
        "public/gym_slot_details.html",
        gym_location=gym_location,
        time_slot=time_slot,
        booked_slot=booked_slot
    )


@app.route("/profile/gym_slot/<booked_slot_id>/delete")
@login_required
def profile_gym_slot_delete(booked_slot_id):
    booked_slot = BookedGymSlot.db.get(booked_slot_id)
    if booked_slot is None:
        flash("Error: Unable to find slot details as it is not in database", "error")
        return redirect(url_for("profile"))

    if booked_slot.user_id != current_user.user_id:
        flash("Error: Unable to cancel slot details not owned by you", "error")
        return redirect(url_for("profile"))

    BookedGymSlot.db.pop(booked_slot_id)
    flash("You have successfully cancelled your booked slot.", "success")
    return redirect(url_for("profile"))


@app.route("/profile/membership", methods=["GET", "POST"])
@login_required
def profile_membership():
    membership_update_form = MembershipUpdateForm(request.form)
    if request.method == "POST" and membership_update_form.validate():
        if membership_update_form.will_renew.data == 'no':
            return redirect(url_for("profile"))
        elif membership_update_form.will_renew.data == 'yes':
            membership = Membership.db.get(current_user.membership_id)
            membership.set_tier_name("NIL")
            Membership.db.set(current_user.membership_id,membership)
            flash("You have successfully cancelled your subscription.", "success")
            return redirect(url_for("profile"))
    return render_template("public/profile_membership.html", form=membership_update_form)


@app.route("/gyms")
def find_a_gym():
    search_gym_form = SearchGymForm(request.args)
    gym_locations = GymLocation.get_all()
    print("gym_locations", gym_locations)
    if search_gym_form.validate():
        gym_locations = GymLocation.filter_by_name(search_gym_form.q.data)
    return render_template("public/gyms.html", form=search_gym_form, gym_locations=gym_locations)


@app.route("/gyms/<gym_id>")
@login_required
def gym_timeslots(gym_id):
    if current_user.is_gym_maxed():
        flash('You can only register a maximum of {} gym time slots!'.format(User.max_gym_slots), 'error')
        return redirect(url_for('profile'))

    gym_location = GymLocation.get(gym_id)
    if gym_location is None:
        flash("Error: Unable to find gym as it is not in the database", "error")
        return redirect(url_for("find_a_gym"))

    time_slots = TimeSlot.filter_by_gym(gym_id)
    time_slots_by_day = TimeSlot.sort_by_day(list(time_slots.values()))

    booked_gym_slots = BookedGymSlot.filter_by_user(current_user.user_id)
    booked_time_slot_ids = []
    for booked_slot in booked_gym_slots:
        time_slot = booked_slot.get_time_slot()
        if time_slot.id in time_slots:
            booked_time_slot_ids.append(time_slot.id)
            break

    return render_template(
        "public/gym_timeslots.html",
        gym_location=gym_location,
        time_slots_by_day=time_slots_by_day,
        booked_time_slot_ids=booked_time_slot_ids,
    )


@app.route("/gyms/<gym_id>/confirm", methods=["GET", "POST"])
@login_required
def gym_confirm(gym_id):
    gym_location = GymLocation.get(gym_id)
    if gym_location is None:
        flash("Error: Unable to find gym as it is not in the database", "error")
        return redirect(url_for("find_a_gym"))

    slot_id = request.args.get("slot_id")
    if slot_id is None:
        flash("No slot id specified", "error")
        return redirect(url_for("gym_timeslots", gym_id=gym_id))

    time_slot = TimeSlot.db.get(slot_id)
    if time_slot is None:
        flash("Could not find time slot in database", "error")
        return redirect(url_for("gym_timeslots", gym_id=gym_id))

    if not time_slot.available:
        flash("That time slot is not available", "error")
        return redirect(url_for("gym_timeslots", gym_id=gym_id))

    booked_gym_slots = BookedGymSlot.filter_by_user(current_user.user_id)
    for booked_slot in booked_gym_slots:
        if time_slot.id == booked_slot.time_slot_id:
            flash("You already booked that time slot", "error")
            return redirect(url_for("gym_timeslots", gym_id=gym_id))

    form = GymCheckoutForm(request.form)
    has_membership = current_user.get_membership().get_tier_name() != "NIL"
    if request.method == "POST" and (has_membership or form.validate()):
        booked_slot = BookedGymSlot(current_user.user_id, gym_id, slot_id, not has_membership)
        flash("Your booking was successfully processed", "success")
        return redirect(url_for("profile_gym_slot", booked_slot_id=booked_slot.id))

    return render_template(
        "public/gym_confirm.html",
        gym_location=gym_location,
        time_slot=time_slot,
        form=form
    )


@app.route("/class_timeslots")
@login_required
def class_timeslots():
    return render_template("public/class_timeslots.html")


@app.route("/class_confirm/<class_name>/<class_time>")
@login_required
def class_confirm(class_name, class_time):
    membership = Membership.db.get(current_user.membership_id)
    if membership.get_tier_name() == 'NIL':
        flash('You need a membership to sign up for classes!', 'error')
        return redirect(url_for("membership_page"))
    start_time, end_time = class_time.split(" - ")
    slot = ClassSlotDetails(current_user.user_id, class_name, start_time, end_time, "www.zoom.com", '17 Feb 2021')
    current_user.add_slot_id(slot.get_id())
    return render_template("public/class_confirm.html", class_name=class_name, class_time=class_time, slot=slot)


@app.route("/class_details/<slot_id>")
@login_required
def class_details(slot_id):
    slot = SlotDetails.db.get(slot_id)
    if slot is None:
        flash("Error: Unable to find slot details as it is not in database", "error")
        return redirect(url_for("profile"))
    return render_template("public/class_details.html", slot=slot)


@app.route("/class_details/<slot_id>/delete")
@login_required
def class_slot_delete(slot_id):
    SlotDetails.db.pop(slot_id)
    current_user.remove_slot_id(slot_id)
    return redirect(url_for("profile"))


@app.route("/membership", methods=["GET", "POST"])
def membership_page():
    return render_template("public/membership.html")


@app.route("/membership/checkout", methods=["GET", "POST"])
@login_required
def membership_checkout():
    membership_checkout_form = MembershipCheckoutForm(request.form)
    if request.method == "POST" and membership_checkout_form.validate():
        tier_choice = membership_checkout_form.tier_choice.data
        membership = Membership.db.get(current_user.membership_id)
        membership.set_tier_name(tier_choice)
        Membership.db.set(current_user.membership_id,membership)
        return redirect(url_for("profile"))
    return render_template("public/membership_checkout.html", form=membership_checkout_form)


@app.route("/faq")
def faq():
    return render_template("public/faq.html")


@app.route("/membership_cancel")
@login_required
def membership_cancel():
    return render_template("public/membership_cancel.html")


@app.route("/contact", methods=['GET', 'POST'])
@login_required
def contact():
    create_user_form = CreateContactForm(request.form)
    if request.method == 'POST' and create_user_form.validate():
        submitted_contact = SubmittedContact(create_user_form.first_name.data,
                                             create_user_form.last_name.data,
                                             create_user_form.location.data,
                                             create_user_form.email.data,
                                             create_user_form.phone.data,
                                             create_user_form.category.data,
                                             create_user_form.message.data
                                             )
        current_user.add_contact_id(submitted_contact.get_id())
        flash("Your form has been submitted successfully!", "success")
        return redirect(url_for('profile_contact_details', form_id=submitted_contact.get_id()))
    return render_template("public/contact.html", form=create_user_form)


@app.route("/profile/<form_id>/profile_contact_detail")
@login_required
def profile_contact_details(form_id):
    contact = SubmittedContact.db.get(form_id)
    print(contact.get_admin_reply())
    return render_template("public/profile_contact_detail.html", contact=contact)


@app.route("/profile/profile_contact")
@login_required
def profile_contact_list():
    all_contact = SubmittedContact.db.dict().values()
    user_contact = []
    print(current_user.contact_id_list)
    for contact in all_contact:
        contact_id = contact.get_id()
        if current_user.contact_id_list.count(contact_id):
            user_contact.append(contact)
    return render_template("public/profile_contact_list.html", user_contact=user_contact)


@app.route("/admin")
@admin_required
def admin_home():
    return render_template("admin/home.html")


@app.route("/admin/gyms", methods=["GET", "POST"])
@admin_required
def admin_gyms():
    gym_added = None
    update_gym_form = CreateGymLocationForm(request.form)
    if request.method == "POST":
        if request.form["form"] == "gym_update":
            if update_gym_form.validate():
                gym_location = GymLocation.db.get(update_gym_form.id.data)
                # check if id is valid
                if gym_location is not None:
                    gym_location.name = update_gym_form.name.data
                    gym_location.address = update_gym_form.address.data
                    gym_location.description = update_gym_form.description.data
                    gym_location.coordinates = Coordinates(
                        lng=update_gym_form.lng.data,
                        lat=update_gym_form.lat.data,
                    )
                    gym_location.capacity_level = CapacityLevel(value=int(update_gym_form.capacity_level.data))

                    GymLocation.db.set(gym_location.id, gym_location)
                    flash(f"{gym_location.name} gym location was successfully updated!", "success")
                else:
                    flash("An error occurred when trying to update gym location.", "error")
            else:
                flash(f"Could not update gym location as input was invalid", "error")
        elif request.form["form"] == "gym_add":
            if update_gym_form.validate():
                gym_location = GymLocation(
                    update_gym_form.name.data,
                    update_gym_form.address.data,
                    update_gym_form.description.data,
                    Coordinates(
                        lng=update_gym_form.lng.data,
                        lat=update_gym_form.lat.data,
                    ),
                    CapacityLevel(value=int(update_gym_form.capacity_level.data))
                )
                gym_added = gym_location

                flash(f"{gym_location.name} gym location was successfully added!", "success")

                update_gym_form = CreateGymLocationForm()  # reset form
            else:
                flash(f"Could not add gym location as input was invalid", "error")

    # search function
    search_gym_form = SearchGymForm(request.args)
    gym_locations = GymLocation.get_all()
    if search_gym_form.validate():
        gym_locations = GymLocation.filter_by_name(search_gym_form.q.data)

    return render_template(
        "admin/gyms.html",
        form=search_gym_form,
        gym_form=update_gym_form,
        gym_locations=gym_locations,
        gym_added=gym_added,
        default_delete_link=url_for("admin_gym_delete", gym_id="X"),
        default_slots_link=url_for("admin_gym_slots", gym_id="X")
    )


@app.route("/admin/gyms/<gym_id>/delete")
@admin_required
def admin_gym_delete(gym_id):
    gym_location = GymLocation.db.pop(gym_id)

    # delete time slots and booked slots if gym deleted
    time_slots = TimeSlot.filter_by_gym(gym_id)
    for time_slot in time_slots.values():
        booked_slots = BookedGymSlot.filter_by_time_slot(time_slot.id)
        for booked_slot in booked_slots:
            BookedGymSlot.db.pop(booked_slot.id)
        TimeSlot.db.pop(time_slot.id)

    flash(f"{gym_location.name} gym location was successfully deleted!", "success")
    return redirect(url_for("admin_gyms"))


@app.template_filter()
def format_day(day: int) -> str:
    return list(calendar.day_name)[day]


@app.template_filter()
def format_date(date: datetime, weekday_included=True) -> str:
    if weekday_included:
        return date.strftime("%A, %d %B %Y")
    else:
        return date.strftime("%d %B %Y")


@app.template_filter()
def format_nearest_day(day: int, weekday_included=True) -> str:
    nearest_date = get_nearest_date_from_day(day)
    return format_date(nearest_date, weekday_included)


@app.template_filter()
def format_time(_time: time) -> str:
    return _time.strftime("%H%M")


@app.route("/admin/gyms/<gym_id>/slots")
@admin_required
def admin_gym_slots(gym_id):
    gym_location = GymLocation.db.get(gym_id)
    if gym_location is None:
        flash("Error: Unable to find gym as it is not in the database", "error")
        return redirect(url_for("admin_gyms"))

    time_slots = TimeSlot.filter_by_gym(gym_id)
    time_slots_by_day = TimeSlot.sort_by_day(list(time_slots.values()))

    return render_template(
        "admin/gym_slots.html",
        gym_location=gym_location,
        time_slots_by_day=time_slots_by_day
    )


@app.route("/admin/gyms/<gym_id>/slot/<slot_id>", methods=["GET", "POST"])
@admin_required
def admin_gym_slot_details(gym_id, slot_id):
    form = UpdateTimeSlotForm(request.form)
    gym_location = GymLocation.db.get(gym_id)
    time_slot = TimeSlot.db.get(slot_id)

    if request.method == "POST" and form.validate():
        time_slot.available = form.available.data
        time_slot.price = form.price.data
        print(form.price.data, type(form.price.data))
        TimeSlot.db.set(time_slot.id, time_slot)
        flash(f"{format_day(time_slot.day)} @ {time_slot} slot was successfully updated!", "success")
        return redirect(url_for("admin_gym_slots", gym_id=gym_id))

    form.available.data = time_slot.available
    form.price.data = time_slot.price

    booked_slots = BookedGymSlot.filter_by_time_slot(slot_id)

    return render_template(
        "admin/gym_slot_details.html",
        form=form,
        gym_location=gym_location,
        time_slot=time_slot,
        booked_slots=booked_slots,
    )


@app.route("/admin/gyms/<gym_id>/slots/<int:day>/add", methods=["GET", "POST"])
@admin_required
def admin_gym_slot_add(day, gym_id):
    form = CreateTimeSlotForm(request.form)
    gym_location = GymLocation.db.get(gym_id)

    time_slots_by_gym = TimeSlot.filter_by_gym(gym_id)
    time_slots = TimeSlot.sort_by_day(list(time_slots_by_gym.values()))[day]
    choices = []

    for hour in range(24):
        # check if a time slot at this hour exists already
        slot_exists = False
        for time_slot in time_slots:
            if time_slot.time.hour == hour:
                slot_exists = True
                break
        # only add this hour as a choice if it doesn't exist yet
        if not slot_exists:
            choices.append((hour, "{}-{}".format(
                format_time(time(hour)),
                format_time(time((hour + 1) % 24))
            )))

    form.time.choices = choices

    if request.method == "POST" and form.validate():
        time_slot = TimeSlot(gym_id, day, time(form.time.data), form.available.data, form.price.data)
        flash(f"{format_day(time_slot.day)} @ {time_slot} slot was successfully added!", "success")

        return redirect(url_for("admin_gym_slots", gym_id=gym_id))

    # set the default choice to the hour after the latest timing
    form.time.data = (time_slots[-1].time.hour + 1) % 24

    return render_template(
        "admin/gym_slot_add.html",
        form=form,
        gym_location=gym_location,
    )


@app.route("/admin/gyms/<gym_id>/slot/<slot_id>/delete", methods=["GET", "POST"])
@admin_required
def admin_gym_slot_delete(gym_id, slot_id):
    time_slot = TimeSlot.db.pop(slot_id)

    # delete booked slots of users who booked this time slot
    booked_slots = BookedGymSlot.filter_by_time_slot(slot_id)
    for booked_slot in booked_slots:
        BookedGymSlot.db.pop(booked_slot.id)

    flash(f"{format_day(time_slot.day)} @ {time_slot} was successfully deleted!", "success")
    return redirect(url_for("admin_gym_slots", gym_id=gym_id))


@app.route("/admin/booked_slot/<booked_slot_id>/delete")
@login_required
def admin_booked_gym_slot_delete(booked_slot_id):
    booked_slot = BookedGymSlot.db.get(booked_slot_id)
    if booked_slot is None:
        flash("Error: Unable to find slot details as it is not in database", "error")
        return redirect(url_for("admin_gyms"))

    BookedGymSlot.db.pop(booked_slot_id)
    flash("You have successfully cancelled the booked slot.", "success")

    next_view = request.args.get("next")
    if next_view is not None:
        return redirect(next_view)
    else:
        return redirect(url_for("admin_gyms"))


@app.route("/admin/contact_forms")
@admin_required
def admin_contact_forms():
    all_contacts = list(SubmittedContact.db.dict().values())
    return render_template("admin/contact_forms.html", all_contacts = all_contacts)


@app.route("/admin/contact_forms/<form_id>/delete")
@admin_required
def admin_contact_form_delete(form_id):
    SubmittedContact.db.pop(form_id)
    return redirect(url_for("admin_contact_forms"))


@app.route("/admin/contact_forms/<form_id>", methods=['GET', 'POST'])
@admin_required
def admin_contact_form_details(form_id):
    contact = SubmittedContact.db.get(form_id)
    form = CreateReplyField(request.form)
    submitted_contact = SubmittedContact.db.get(form_id)
    if request.method == "POST" and form.validate():
        submitted_contact.set_admin_reply(form.reply.data)
        SubmittedContact.db.set(submitted_contact.get_id(), submitted_contact)
        flash("Your reply have been submitted successfully!", "success")
    form.reply.data = submitted_contact.get_admin_reply()
    return render_template("admin/contact_form_details.html", contact = contact, form = form)


@app.route("/admin/class_slots")
@admin_required
def admin_class_slots():
    all_classes = {}
    users = list(User.db.dict().values())
    for user in users:
        user_class_slots = []
        for slot_id in user.slot_id_list:
            class_slot = SlotDetails.db.get(slot_id)
            user_class_slots.append(class_slot)
        all_classes[user.username] = user_class_slots
    return render_template("admin/class_slots.html", all_classes=all_classes)


@app.route("/admin/class_slots/<slot_id>/delete")
@login_required
def admin_class_slots_delete(slot_id):
    slot = SlotDetails.db.pop(slot_id)
    user = User.db.get(slot.get_user_id())
    user.remove_slot_id(slot_id)
    return redirect(url_for("admin_class_slots"))


@app.route("/admin/check_membership")
@admin_required
def admin_check_membership():
    all_members = {}
    users = list(User.db.dict().values())
    for user in users:
        membership = Membership.db.get(user.membership_id)
        all_members[user.username] = membership.get_tier_name()
    return render_template("admin/check_membership.html", all_members=all_members)


# generate random gym locations every time the program is run
# remove when adding of gym locations feature is done
generate_random_locations()
generate_admin_user()

if __name__ == "__main__":
    app.run()

